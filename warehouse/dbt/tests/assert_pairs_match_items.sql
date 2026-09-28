-- Over each tenant's last 30 days, agg_daily_pair summed over days and segments equals a direct
-- recount of co-orders from fct_order_items.
with windows as (
  select
    tenant_id,
    max(order_day) - 29 as start_day
  from {{ ref('fct_order_items') }}
  group by tenant_id
),

items as (
  select
    i.tenant_id,
    i.order_id,
    i.sku
  from {{ ref('fct_order_items') }} as i
  inner join windows as w on i.tenant_id = w.tenant_id
  where i.order_day >= w.start_day
),

recount as (
  select
    a.tenant_id,
    a.sku as sku_a,
    b.sku as sku_b,
    count(*) as n_orders
  from items as a
  inner join items as b
    on
      a.tenant_id = b.tenant_id
      and a.order_id = b.order_id
      and a.sku < b.sku collate "C"
  group by a.tenant_id, a.sku, b.sku
),

agg as (
  select
    p.tenant_id,
    p.sku_a,
    p.sku_b,
    sum(p.n_orders) as n_orders
  from {{ ref('agg_daily_pair') }} as p
  inner join windows as w on p.tenant_id = w.tenant_id
  where p.day >= w.start_day
  group by p.tenant_id, p.sku_a, p.sku_b
)

select
  coalesce(r.tenant_id, a.tenant_id) as tenant_id,
  coalesce(r.sku_a, a.sku_a) as sku_a,
  coalesce(r.sku_b, a.sku_b) as sku_b,
  r.n_orders as recounted,
  a.n_orders as aggregated
from recount as r
full outer join agg as a
  on r.tenant_id = a.tenant_id and r.sku_a = a.sku_a and r.sku_b = a.sku_b
where r.n_orders is distinct from a.n_orders
