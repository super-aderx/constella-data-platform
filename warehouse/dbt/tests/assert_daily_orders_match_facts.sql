-- The daily aggregate counts every paid order exactly once, per tenant.
with facts as (
  select
    tenant_id,
    count(*) as n_orders,
    sum(total_cents) as revenue_cents
  from {{ ref('fct_orders') }}
  where status = 'paid'
  group by tenant_id
),

agg as (
  select
    tenant_id,
    sum(n_orders) as n_orders,
    sum(revenue_cents) as revenue_cents
  from {{ ref('agg_daily_orders') }}
  group by tenant_id
)

select
  coalesce(f.tenant_id, a.tenant_id) as tenant_id,
  f.n_orders as fact_orders,
  a.n_orders as agg_orders
from facts as f
full outer join agg as a on f.tenant_id = a.tenant_id
where
  f.n_orders is distinct from a.n_orders
  or f.revenue_cents is distinct from a.revenue_cents
