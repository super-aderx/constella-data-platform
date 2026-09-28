"""P0 acceptance checks (warehouse_spec.md, "P0 acceptance"), read the way Constella reads:
as api_reader, through serving views, with app.tenant_id set per transaction.

    uv run --env-file ../.env python scripts/acceptance.py

Exits non-zero if any check fails.
"""

import os
import sys
from collections import Counter
from datetime import timedelta
from pathlib import Path

import networkx as nx
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generator.tenants import all_tenants  # noqa: E402

TENANT_VIEWS = (
    "categories",
    "products",
    "daily_orders",
    "daily_product",
    "daily_pair",
    "freshness",
)
EXPECTED_ORDERS_90D = 24_120
MIN_SEGMENT_SHARE = 0.03

# warehouse_spec.md, "Backend integration": the query fetch_edges will run.
EDGES_SQL = """
with n as (
  select sum(n_orders)::float as n from serving.daily_orders
  where tenant_id = %(t)s and day between %(start)s and %(end)s
    and (%(segment)s = 'all' or segment = %(segment)s)
),
p as (
  select sku, sum(n_orders) as n from serving.daily_product
  where tenant_id = %(t)s and day between %(start)s and %(end)s
    and (%(segment)s = 'all' or segment = %(segment)s)
  group by sku
),
e as (
  select sku_a, sku_b, sum(n_orders) as c from serving.daily_pair
  where tenant_id = %(t)s and day between %(start)s and %(end)s
    and (%(segment)s = 'all' or segment = %(segment)s)
  group by sku_a, sku_b
  having sum(n_orders) >= %(min_co_orders)s
)
select e.sku_a, e.sku_b, e.c as co_orders,
       e.c / n.n              as support,
       e.c::float / pa.n      as conf_a_to_b,
       e.c::float / pb.n      as conf_b_to_a,
       e.c * n.n / (pa.n * pb.n) as lift
from e
join p pa on pa.sku = e.sku_a
join p pb on pb.sku = e.sku_b
cross join n
where e.c * n.n / (pa.n * pb.n) >= %(min_lift)s
order by lift desc, e.sku_a, e.sku_b
limit %(limit)s
"""

failures: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("  ok    " if ok else "  FAIL  ") + message)
    if not ok:
        failures.append(message)


def as_tenant(conn: psycopg.Connection, tenant_id) -> None:
    conn.execute("select set_config('app.tenant_id', %s, true)", (str(tenant_id),))


def main() -> None:
    tenants = all_tenants()
    hs, mc = tenants["harbor-street"], tenants["maple-corner"]
    conn = psycopg.connect(os.environ["DATABASE_URL"])

    print("Isolation")
    with conn.transaction():
        counts = {v: conn.execute(f"select count(*) from serving.{v}").fetchone()[0]
                  for v in TENANT_VIEWS}  # fmt: skip
    check(all(c == 0 for c in counts.values()), f"no rows without app.tenant_id: {counts}")
    with conn.transaction():
        as_tenant(conn, mc.tenant_id)
        others = sum(
            conn.execute(f"select count(*) from serving.{v} where tenant_id <> %s",
                         (mc.tenant_id,)).fetchone()[0]
            for v in TENANT_VIEWS
        )  # fmt: skip
        hs_skus = conn.execute(
            """
            select (select count(*) from serving.products where sku like 'HS-%%')
                 + (select count(*) from serving.daily_product where sku like 'HS-%%')
                 + (select count(*) from serving.daily_pair
                    where sku_a like 'HS-%%' or sku_b like 'HS-%%')
            """
        ).fetchone()[0]
    check(others == 0 and hs_skus == 0, "as Maple Corner, no other tenant's rows or HS- SKUs")
    try:
        with conn.transaction():
            conn.execute("select 1 from gold.agg_daily_pair limit 1")
        check(False, "api_reader can't read gold")
    except psycopg.errors.InsufficientPrivilege:
        check(True, "api_reader can't read gold")

    print("Harbor Street, 90 days ending last_complete_day")
    with conn.transaction():
        as_tenant(conn, hs.tenant_id)
        end = conn.execute("select last_complete_day from serving.freshness").fetchone()[0]
        start = end - timedelta(days=89)
        by_segment = dict(
            conn.execute(
                """
                select segment, sum(n_orders) from serving.daily_orders
                where tenant_id = %s and day between %s and %s group by segment
                """,
                (hs.tenant_id, start, end),
            ).fetchall()
        )
        params = dict(t=hs.tenant_id, start=start, end=end, segment="all", min_co_orders=5,
                      min_lift=1.0, limit=5000)  # fmt: skip
        edges = conn.execute(EDGES_SQL, params).fetchall()

    n = sum(by_segment.values())
    check(
        abs(n - EXPECTED_ORDERS_90D) <= EXPECTED_ORDERS_90D * 0.1,
        f"{n:,} paid orders {start}..{end} (expected {EXPECTED_ORDERS_90D:,} ± 10%)",
    )
    shares = {s: c / n for s, c in sorted(by_segment.items(), key=lambda kv: -kv[1])}
    check(
        len(shares) == 6 and min(shares.values()) >= MIN_SEGMENT_SHARE,
        "every segment ≥ 3% of orders: " + ", ".join(f"{s} {v:.1%}" for s, v in shares.items()),
    )

    g = nx.Graph()
    for sku_a, sku_b, co_orders, *_, lift in edges:
        g.add_edge(sku_a, sku_b, lift=lift, co_orders=co_orders)
    theme = {hs.sku(p.code): p.theme for p in hs.products}
    communities = nx.community.louvain_communities(g, weight="lift", seed=42)
    placed = 0
    for members in communities:
        themes = Counter(theme[s] for s in members if theme.get(s))
        if themes:
            placed += themes.most_common(1)[0][1]
    themed = sum(1 for s in g.nodes if theme.get(s))
    check(placed >= 26, f"{placed} of {themed} themed products in their theme's community")
    cut = set(nx.articulation_points(g))
    check(
        {"HS-MILK", "HS-CHEDDAR"} <= cut and bool({"HS-PARMESAN", "HS-EGGS"} & cut),
        f"articulation points include Whole Milk, Cheddar, Parmesan or Eggs: {sorted(cut)}",
    )

    conn.close()
    if failures:
        raise SystemExit(f"{len(failures)} acceptance check(s) failed")
    print("All P0 acceptance checks passed")


if __name__ == "__main__":
    main()
