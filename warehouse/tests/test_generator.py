from collections import Counter
from datetime import date

import pytest

from generator.load import bronze_rows
from generator.simulate import simulate
from generator.tenants import all_tenants

END = date(2026, 9, 26)
DAYS = 21


@pytest.fixture(scope="module", params=list(all_tenants()))
def run(request):
    spec = all_tenants()[request.param]
    events, stats = simulate(spec, DAYS, END, seed=42)
    return spec, events, stats


def test_same_arguments_give_identical_rows(run):
    spec, events, _ = run
    again, _ = simulate(spec, DAYS, END, seed=42)
    assert bronze_rows(spec, events, 42, 0.02, 0.01) == bronze_rows(spec, again, 42, 0.02, 0.01)


def test_messiness_never_changes_business_events(run):
    spec, events, _ = run
    clean = bronze_rows(spec, events, 42, 0.0, 0.0)
    messy = bronze_rows(spec, events, 42, 0.2, 0.05)
    assert len(messy) > len(clean)
    # Same set of (event_id, payload), whatever the duplicates and load order.
    assert {(r[1], r[7]) for r in messy} == {(r[1], r[7]) for r in clean}
    # Offsets are unique per topic and partition, as the bronze unique key requires.
    assert len({(r[8], r[9], r[10]) for r in messy}) == len(messy)


def test_order_payload_invariants(run):
    _, events, _ = run
    placed = [e.payload for e in events if e.event_type == "OrderPlaced"]
    assert placed
    for p in placed:
        skus = [i["sku"] for i in p["items"]]
        assert len(skus) == len(set(skus))
        assert all(i["line_total_cents"] == i["qty"] * i["unit_price_cents"] for i in p["items"])
        assert p["subtotal_cents"] == sum(i["line_total_cents"] for i in p["items"])
        assert p["total_cents"] == p["subtotal_cents"] - p["discount_cents"] >= 0


def test_every_order_ends_paid_or_cancelled(run):
    _, events, stats = run
    kinds = Counter(e.event_type for e in events)
    assert kinds["OrderPlaced"] == stats.orders == stats.paid + stats.cancelled
    assert kinds["OrderPaid"] == stats.paid
    assert kinds["OrderCancelled"] == stats.cancelled


def test_customers_register_before_they_order(run):
    _, events, _ = run
    registered = {}
    for e in events:  # in occurred_at order
        if e.event_type == "CustomerRegistered":
            registered[e.payload["customer_id"]] = e.occurred_at
        elif e.event_type == "OrderPlaced":
            assert e.payload["customer_id"] in registered
