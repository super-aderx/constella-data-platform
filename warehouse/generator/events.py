"""TPS v1 event envelopes and payloads, as StarMart's outbox publishes them (tps_spec.md)."""

import random
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

SCHEMA_VERSION = 1


def uuid7(ts: datetime, rng: random.Random) -> uuid.UUID:
    """A UUIDv7 for a (simulated) time, with seeded random bits so output is reproducible."""
    ms = int(ts.timestamp() * 1000)
    value = (
        (ms & 0xFFFF_FFFF_FFFF) << 80
        | 0x7 << 76
        | rng.getrandbits(12) << 64
        | 0b10 << 62
        | rng.getrandbits(62)
    )
    return uuid.UUID(int=value)


def to_ms(ts: datetime) -> datetime:
    """Truncate to milliseconds, the precision of RFC 3339 timestamps in payloads."""
    return ts.replace(microsecond=ts.microsecond // 1000 * 1000)


def rfc3339(ts: datetime) -> str:
    ts = ts.astimezone(UTC)
    return ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"


@dataclass(frozen=True, slots=True)
class Event:
    event_id: uuid.UUID
    event_type: str
    occurred_at: datetime
    aggregate_type: str  # the outbox's aggregate type; names the topic
    aggregate_id: str
    trace_id: str
    payload: dict


class EventFactory:
    """Builds envelopes. All randomness (ids, trace ids) comes from one seeded generator."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    def id(self, ts: datetime) -> uuid.UUID:
        return uuid7(ts, self.rng)

    def trace(self) -> str:
        return f"{self.rng.getrandbits(128):032x}"

    def _event(
        self, event_type: str, at: datetime, agg_type: str, agg_id, payload: dict, trace: str
    ) -> Event:
        return Event(self.id(at), event_type, at, agg_type, str(agg_id), trace, payload)

    # --- catalog ---

    def category(self, kind: str, at: datetime, category_id, parent_id, name: str, slug: str):
        payload = {
            "category_id": str(category_id),
            "parent_id": str(parent_id) if parent_id else None,
            "name": name,
            "slug": slug,
        }
        return self._event(f"Category{kind}", at, "category", category_id, payload, self.trace())

    def product(
        self,
        kind: str,
        at: datetime,
        product_id,
        sku: str,
        name: str,
        brand: str,
        category_id,
        unit: str,
        size: str,
        status: str,
    ):
        payload = {
            "product_id": str(product_id),
            "sku": sku,
            "name": name,
            "brand": brand,
            "category_id": str(category_id),
            "unit": unit,
            "size": size,
            "status": status,
        }
        return self._event(f"Product{kind}", at, "product", sku, payload, self.trace())

    def price_changed(self, at: datetime, sku: str, amount_cents: int, currency: str):
        payload = {
            "sku": sku,
            "amount_cents": amount_cents,
            "currency": currency,
            "valid_from": rfc3339(at),
        }
        return self._event("PriceChanged", at, "product", sku, payload, self.trace())

    # --- customers ---

    def customer(self, kind: str, at: datetime, customer_id, status: str, registered_at):
        payload = {
            "customer_id": str(customer_id),
            "status": status,
            "registered_at": rfc3339(registered_at),
        }
        return self._event(f"Customer{kind}", at, "customer", customer_id, payload, self.trace())

    # --- orders and payments ---

    def order_placed(
        self, at: datetime, order_id, customer_id, currency: str, items: list[dict], trace: str
    ):
        subtotal = sum(i["line_total_cents"] for i in items)
        payload = {
            "order_id": str(order_id),
            "customer_id": str(customer_id),
            "placed_at": rfc3339(at),
            "currency": currency,
            "subtotal_cents": subtotal,
            "discount_cents": 0,
            "total_cents": subtotal,
            "items": items,
            "discounts": [],
        }
        return self._event("OrderPlaced", at, "order", order_id, payload, trace)

    def payment(
        self,
        at: datetime,
        order_id,
        attempt: int,
        amount_cents: int,
        failure_code: str | None,
        trace: str,
    ):
        payment_id = self.id(at)
        payload = {
            "payment_id": str(payment_id),
            "order_id": str(order_id),
            "attempt": attempt,
            "amount_cents": amount_cents,
            "failure_code": failure_code,
        }
        kind = "PaymentFailed" if failure_code else "PaymentSucceeded"
        return self._event(kind, at, "payment", order_id, payload, trace)

    def order_paid(self, at: datetime, order_id, trace: str):
        payload = {"order_id": str(order_id), "paid_at": rfc3339(at)}
        return self._event("OrderPaid", at, "order", order_id, payload, trace)

    def order_cancelled(self, at: datetime, order_id, reason: str, trace: str):
        payload = {"order_id": str(order_id), "cancelled_at": rfc3339(at), "reason": reason}
        return self._event("OrderCancelled", at, "order", order_id, payload, trace)
