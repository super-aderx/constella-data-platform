"""Tenant definitions: catalog, basket themes, planted bridges and volumes."""

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CategorySpec:
    slug: str
    name: str
    parent: str | None = None  # parent slug; two levels at most
    # (days before --end, name it had until then): a CategoryUpdated rename during the period.
    renamed_from: tuple[int, str] | None = None


@dataclass(frozen=True)
class ProductSpec:
    code: str  # the SKU is <sku_prefix><code>
    name: str
    category: str  # category slug
    brand: str
    unit: str
    size: str
    price_cents: int  # current price
    theme: str | None
    # Chance the product is picked when its theme is in a basket (before the persona's scale).
    p: float = 0.0
    # Chance it's added to any regular basket, independent of themes (unthemed products).
    addon_p: float = 0.0
    # (days before --end, price in cents until then): a PriceChanged during the period.
    earlier_price: tuple[int, int] | None = None
    # (days before --end, name until then): a ProductUpdated rename.
    renamed_from: tuple[int, str] | None = None
    # Days before --end it's set inactive (ProductUpdated); it isn't sold after that.
    discontinued: int | None = None


@dataclass(frozen=True)
class Bridge:
    """When `theme` is in a basket (and `requires` is too, if set), add `add` with chance `p`."""

    theme: str
    add: str
    p: float
    requires: str | None = None


@dataclass(frozen=True)
class TenantSpec:
    key: str
    name: str
    timezone: str
    currency: str
    sku_prefix: str
    categories: tuple[CategorySpec, ...]
    products: tuple[ProductSpec, ...]
    theme_weights: dict[str, float]
    bridges: tuple[Bridge, ...] = ()
    # Share of orders that are quick errands: one or two items, outside any theme.
    errand_rate: float = 0.05
    errand_weights: dict[str, float] = field(default_factory=dict)  # code -> weight
    # Chance a regular basket gets one random product. Kept low so unrelated pairs stay below
    # lift 1.
    noise_rate: float = 0.04
    # Persona -> theme -> multiplier on theme_weights, so segments differ in what they buy.
    affinity: dict[str, dict[str, float]] = field(default_factory=dict)
    # Customers already registered before the first simulated day, and new ones per day.
    initial_customers: int = 2000
    arrivals_per_day: float = 4.0

    @property
    def tenant_id(self) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_URL, f"constella:tenant:{self.key}")

    def sku(self, code: str) -> str:
        return f"{self.sku_prefix}{code}"


def all_tenants() -> dict[str, TenantSpec]:
    from generator.tenants.harbor_street import HARBOR_STREET
    from generator.tenants.maple_corner import MAPLE_CORNER

    return {t.key: t for t in (HARBOR_STREET, MAPLE_CORNER)}
