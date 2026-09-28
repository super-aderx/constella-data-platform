"""Simulates one tenant's shop and returns its business events in occurred_at order.

Deterministic: everything comes from one generator seeded by (seed, tenant key), so the same
arguments give the same events. Loading messiness lives in load.py with its own generator,
so changing --duplicate-rate or --late-rate never changes the business data.
"""

import bisect
import math
import random
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from generator.events import Event, EventFactory, to_ms
from generator.personas import BY_NAME, CHURN, PERSONAS, REGULARS, Persona
from generator.tenants import ProductSpec, TenantSpec

# Orders happen during store hours, 08:00-22:00 local, with lunchtime and evening peaks.
OPEN_HOUR, CLOSE_HOUR = 8, 22
# The day after --end is written up to 09:00 local, as a live shop's in-progress day.
IN_PROGRESS_UNTIL = time(9, 0)

# Payment outcomes (tps_spec.md mock provider): 92% paid first time; 6% fail, half of those
# retry and succeed, the rest fail three times and are cancelled; 2% time out and are then
# cancelled by the customer or by the 15-minute timeout.
FAIL_P = 0.06
RETRY_SUCCEEDS_P = 0.5
ABANDON_P = 0.02
DECLINE_CODES = ("insufficient_funds", "card_expired", "do_not_honor")
MAX_ATTEMPTS = 3
UNPAID_TIMEOUT = timedelta(minutes=15)


@dataclass
class Stats:
    customers: int = 0
    orders: int = 0
    paid: int = 0
    cancelled: int = 0
    events: int = 0


@dataclass
class Catalog:
    """Per-SKU price and availability over time, for pricing orders at checkout."""

    price_changes: dict[str, list[tuple[datetime, int]]] = field(default_factory=dict)
    inactive_from: dict[str, datetime] = field(default_factory=dict)

    def price(self, sku: str, at: datetime) -> int:
        changes = self.price_changes[sku]
        i = bisect.bisect_right([t for t, _ in changes], at) - 1
        return changes[max(i, 0)][1]

    def active(self, sku: str, at: datetime) -> bool:
        return sku not in self.inactive_from or at < self.inactive_from[sku]


def _poisson(rng: random.Random, lam: float) -> int:
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def _weighted(rng: random.Random, weights: dict[str, float]) -> str:
    keys = list(weights)
    return rng.choices(keys, weights=[weights[k] for k in keys])[0]


class Simulation:
    def __init__(self, spec: TenantSpec, days: int, end: date, seed: int):
        self.spec = spec
        self.tz = ZoneInfo(spec.timezone)
        self.start = end - timedelta(days=days - 1)
        self.end = end
        self.horizon = self.local(end + timedelta(days=1), IN_PROGRESS_UNTIL)
        self.rng = random.Random(f"{seed}/{spec.key}/sim")
        self.f = EventFactory(self.rng)
        self.events: list[Event] = []
        self.catalog = Catalog()
        self.stats = Stats()
        self.products = {p.code: p for p in spec.products}
        self.themes: dict[str, list[ProductSpec]] = {}
        for p in spec.products:
            if p.theme:
                self.themes.setdefault(p.theme, []).append(p)
        self.addons = [p for p in spec.products if p.addon_p]

    def local(self, day: date, at: time) -> datetime:
        """A local wall-clock time on a day, as UTC at millisecond precision."""
        return to_ms(datetime.combine(day, at, self.tz).astimezone(UTC))

    def day_before_end(self, days: int, at: time = time(6, 0)) -> datetime:
        return self.local(self.end - timedelta(days=days), at)

    def emit(self, event: Event) -> None:
        self.events.append(event)

    # --- catalog ---

    def build_catalog(self) -> None:
        spec, f = self.spec, self.f
        # A week before the first simulated day, or before the earliest catalog change if a short
        # --days would otherwise put a rename, price change or discontinuation before creation.
        offsets = [c.renamed_from[0] for c in spec.categories if c.renamed_from]
        for p in spec.products:
            offsets += [p.renamed_from[0]] if p.renamed_from else []
            offsets += [p.earlier_price[0]] if p.earlier_price else []
            offsets += [p.discontinued] if p.discontinued is not None else []
        first_change = self.end - timedelta(days=max(offsets, default=0) + 1)
        opened = self.local(min(self.start - timedelta(days=7), first_change), time(6, 0))
        ids: dict[str, object] = {}

        for i, c in enumerate(spec.categories):
            at = opened + timedelta(seconds=i)
            ids[c.slug] = f.id(at)
            parent = ids[c.parent] if c.parent else None
            first_name = c.renamed_from[1] if c.renamed_from else c.name
            self.emit(f.category("Created", at, ids[c.slug], parent, first_name, c.slug))
            if c.renamed_from:
                renamed = self.day_before_end(c.renamed_from[0])
                self.emit(f.category("Updated", renamed, ids[c.slug], parent, c.name, c.slug))

        for i, p in enumerate(spec.products):
            at = opened + timedelta(hours=1, seconds=i)
            sku, pid, cat = spec.sku(p.code), f.id(at), ids[p.category]
            state = dict(sku=sku, name=p.name, brand=p.brand, category_id=cat, unit=p.unit,
                         size=p.size, status="active")  # fmt: skip
            if p.renamed_from:
                state["name"] = p.renamed_from[1]
            self.emit(f.product("Created", at, pid, **state))

            price = p.earlier_price[1] if p.earlier_price else p.price_cents
            self.emit(f.price_changed(at, sku, price, spec.currency))
            self.catalog.price_changes[sku] = [(at, price)]
            if p.earlier_price:
                changed = self.day_before_end(p.earlier_price[0])
                self.emit(f.price_changed(changed, sku, p.price_cents, spec.currency))
                self.catalog.price_changes[sku].append((changed, p.price_cents))

            if p.renamed_from:
                state["name"] = p.name
                renamed = self.day_before_end(p.renamed_from[0], time(6, 5))
                self.emit(f.product("Updated", renamed, pid, **state))
            if p.discontinued is not None:
                state["status"] = "inactive"
                off = self.day_before_end(p.discontinued, time(6, 10))
                self.emit(f.product("Updated", off, pid, **state))
                self.catalog.inactive_from[sku] = off

    # --- customers ---

    def order_time(self, rng: random.Random, day: date) -> datetime:
        r = rng.random()
        if r < 0.3:
            hour = rng.gauss(12.5, 1.0)
        elif r < 0.75:
            hour = rng.gauss(18.5, 1.5)
        else:
            hour = rng.uniform(OPEN_HOUR, CLOSE_HOUR)
        hour = min(max(hour, OPEN_HOUR), CLOSE_HOUR - 1e-6)
        # Build the local wall-clock time before converting, so DST days keep store hours.
        seconds = int(hour * 3600)
        at = time(seconds // 3600, seconds // 60 % 60, seconds % 60)
        return self.local(day, at) + timedelta(milliseconds=rng.randrange(1000))

    def order_days(self, rng: random.Random, persona: Persona, first: float) -> list[float]:
        """Order times in days since the first simulated day's midnight."""
        horizon = (self.end - self.start).days + 2  # through the in-progress day
        if persona.mean_gap_days is None:
            return [first] if first < horizon else []

        mean_gap = rng.uniform(*persona.mean_gap_days)
        churn_at = rng.uniform(first, horizon) if rng.random() < CHURN.rate else None
        stop_at = churn_at + rng.uniform(*CHURN.slowdown_days) if churn_at is not None else None

        days, t = [], first
        while t < horizon and (stop_at is None or t < stop_at):
            days.append(t)
            gap = rng.gammavariate(persona.gap_shape, mean_gap / persona.gap_shape)
            if rng.random() < persona.pause_p:
                gap *= rng.uniform(3, 6)
            if churn_at is not None and t >= churn_at:
                gap *= CHURN.slowdown_gap_factor
            t += max(gap, 0.5)
        if stop_at is not None and rng.random() < CHURN.winback_p:
            back = (days[-1] if days else t) + rng.uniform(*CHURN.winback_after_days)
            if back < horizon:
                days.append(back)
        return days

    def simulate_customer(self, persona: Persona, registered_at: datetime, first: float) -> None:
        f = self.f
        rng = random.Random(self.rng.getrandbits(64))
        customer_id = f.id(registered_at)
        self.emit(f.customer("Registered", registered_at, customer_id, "active", registered_at))
        self.stats.customers += 1

        last_at = registered_at
        for t in self.order_days(rng, persona, first):
            day = self.start + timedelta(days=int(t))
            if day > self.end:
                # The in-progress day: only its first hour of trading, about 1/14 of a day.
                if rng.random() >= 1 / (CLOSE_HOUR - OPEN_HOUR):
                    break
                placed_at = self.local(day, time(OPEN_HOUR)) + timedelta(
                    milliseconds=rng.randrange(3_600_000)
                )
            else:
                placed_at = self.order_time(rng, day)
            if placed_at <= last_at:
                placed_at = last_at + timedelta(minutes=rng.randint(20, 240))
            if placed_at >= self.horizon:
                break
            self.place_order(rng, persona, customer_id, placed_at)
            last_at = placed_at

        # Some churned customers delete their account a while after their last order.
        churned = persona in REGULARS and last_at < self.horizon - timedelta(days=150)
        if churned and rng.random() < CHURN.delete_p:
            deleted_at = to_ms(last_at + timedelta(days=rng.uniform(30, 120)))
            if deleted_at < self.horizon:
                self.emit(f.customer("Updated", deleted_at, customer_id, "deleted", registered_at))

    def build_customers(self) -> None:
        spec, rng = self.spec, self.rng
        regular_shares = {p.name: p.share for p in REGULARS}
        all_shares = {p.name: p.share for p in PERSONAS}

        # Customers from before the simulated period: registered in the two years before it,
        # first seen at a random point in their first gap.
        for _ in range(spec.initial_customers):
            persona = BY_NAME[_weighted(rng, regular_shares)]
            registered_at = to_ms(
                self.local(self.start, time(0)) - timedelta(seconds=rng.uniform(86400, 730 * 86400))
            )
            first = rng.uniform(0, persona.mean_gap_days[1])
            self.simulate_customer(persona, registered_at, first)

        # New customers register every day and usually order within a few days.
        for offset in range((self.end - self.start).days + 1):
            day = self.start + timedelta(days=offset)
            for _ in range(_poisson(rng, spec.arrivals_per_day)):
                persona = BY_NAME[_weighted(rng, all_shares)]
                registered_at = self.order_time(rng, day) - timedelta(minutes=rng.randint(5, 60))
                first = offset + (0 if rng.random() < 0.6 else rng.uniform(1, 4))
                self.simulate_customer(persona, registered_at, first)

    # --- orders ---

    def basket(self, rng: random.Random, persona: Persona, at: datetime) -> dict[str, int]:
        spec = self.spec
        picked: set[str] = set()

        if rng.random() < spec.errand_rate:
            for _ in range(1 if rng.random() < 0.6 else 2):
                picked.add(_weighted(rng, spec.errand_weights))
        else:
            affinity = spec.affinity.get(persona.name, {})
            weights = {t: w * affinity.get(t, 1.0) for t, w in spec.theme_weights.items()}
            themes = [_weighted(rng, weights)]
            if rng.random() < persona.second_theme_p:
                del weights[themes[0]]
                themes.append(_weighted(rng, weights))
            for theme in themes:
                members = self.themes[theme]
                chosen: list[str] = []
                while not chosen:
                    chosen = [
                        p.code
                        for p in members
                        if rng.random() < min(p.p * persona.basket_scale, 0.95)
                    ]
                picked.update(chosen)
            for b in spec.bridges:
                applies = b.theme in themes and (b.requires is None or b.requires in picked)
                if applies and rng.random() < b.p:
                    picked.add(b.add)
            for p in self.addons:
                if rng.random() < p.addon_p:
                    picked.add(p.code)
            if rng.random() < spec.noise_rate:
                picked.add(rng.choice(spec.products).code)

        basket = {}
        for code in sorted(picked):
            sku = spec.sku(code)
            if not self.catalog.active(sku, at):
                continue
            qty = (
                1 + (rng.random() < persona.extra_qty_p) + (rng.random() < persona.extra_qty_p / 3)
            )
            basket[sku] = qty
        return basket

    def place_order(
        self, rng: random.Random, persona: Persona, customer_id, placed_at: datetime
    ) -> None:
        f = self.f
        basket = self.basket(rng, persona, placed_at)
        if not basket:
            return
        items = []
        for sku, qty in basket.items():
            unit = self.catalog.price(sku, placed_at)
            items.append(
                {"sku": sku, "qty": qty, "unit_price_cents": unit, "line_total_cents": unit * qty}
            )
        order_id = f.id(placed_at)
        trace = f.trace()
        placed = f.order_placed(placed_at, order_id, customer_id, self.spec.currency, items, trace)
        self.emit(placed)
        total = placed.payload["total_cents"]
        self.stats.orders += 1

        at = placed_at + timedelta(milliseconds=rng.randint(100, 800))
        r = rng.random()
        if r < ABANDON_P:
            self.emit(f.payment(at, order_id, 1, total, "provider_timeout", trace))
            if rng.random() < 0.5:
                cancelled_at = at + timedelta(seconds=rng.uniform(60, 600))
                reason = "customer"
            else:
                cancelled_at, reason = placed_at + UNPAID_TIMEOUT, "timeout"
            self.emit(f.order_cancelled(to_ms(cancelled_at), order_id, reason, trace))
            self.stats.cancelled += 1
            return

        attempts = 1
        if r < ABANDON_P + FAIL_P:
            self.emit(f.payment(at, order_id, 1, total, rng.choice(DECLINE_CODES), trace))
            succeeds = rng.random() < RETRY_SUCCEEDS_P
            last_attempt = 2 if succeeds else MAX_ATTEMPTS
            for attempts in range(2, last_attempt + 1):
                at = to_ms(at + timedelta(seconds=rng.uniform(20, 240)))
                code = None if succeeds else rng.choice(DECLINE_CODES)
                self.emit(f.payment(at, order_id, attempts, total, code, trace))
            if not succeeds:
                cancelled_at = to_ms(at + timedelta(milliseconds=rng.randint(10, 60)))
                self.emit(f.order_cancelled(cancelled_at, order_id, "payment_failed", trace))
                self.stats.cancelled += 1
                return
        else:
            self.emit(f.payment(to_ms(at), order_id, 1, total, None, trace))

        paid_at = to_ms(at + timedelta(milliseconds=rng.randint(5, 50)))
        self.emit(f.order_paid(paid_at, order_id, trace))
        self.stats.paid += 1

    def run(self) -> list[Event]:
        self.build_catalog()
        self.build_customers()
        self.events.sort(key=lambda e: (e.occurred_at, e.event_id))
        self.stats.events = len(self.events)
        return self.events


def simulate(spec: TenantSpec, days: int, end: date, seed: int) -> tuple[list[Event], Stats]:
    sim = Simulation(spec, days, end, seed)
    return sim.run(), sim.stats
