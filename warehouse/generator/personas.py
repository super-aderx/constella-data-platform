"""Customer behaviour, following the StarMart simulator's personas (tps_spec.md)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    name: str
    share: float  # of customers
    # Each customer draws a mean gap between orders from this range (days); None = one order.
    mean_gap_days: tuple[float, float] | None
    # Gamma shape for each gap: high = like clockwork, 1 = memoryless.
    gap_shape: float
    # Multiplies each product's chance of being picked from a theme: bigger or smaller baskets.
    basket_scale: float
    # Chance an order covers a second theme.
    second_theme_p: float
    # Chance a line has qty 2 (and a third of it again for qty 3).
    extra_qty_p: float
    # Chance a gap is a break (holiday, busy month): 3-6 times as long.
    pause_p: float = 0.0


PERSONAS = (
    Persona("weekly_stocker", 0.40, (6, 8), 8.0, 1.25, 0.45, 0.35, pause_p=0.06),
    Persona("deal_hunter", 0.25, (10, 20), 4.0, 1.0, 0.25, 0.25, pause_p=0.08),
    Persona("browser", 0.25, (25, 240), 1.0, 0.75, 0.08, 0.10),
    Persona("one_time", 0.10, None, 1.0, 0.9, 0.15, 0.15),
)
BY_NAME = {p.name: p for p in PERSONAS}
REGULARS = tuple(p for p in PERSONAS if p.mean_gap_days)


@dataclass(frozen=True)
class Churn:
    """About 15% of regulars slow down, then stop; some come back once much later."""

    rate: float = 0.15
    slowdown_days: tuple[float, float] = (60, 150)
    slowdown_gap_factor: float = 3.5
    winback_p: float = 0.5
    winback_after_days: tuple[float, float] = (100, 240)
    # Share of churned customers who later delete their account (CustomerUpdated, deleted).
    delete_p: float = 0.1


CHURN = Churn()
