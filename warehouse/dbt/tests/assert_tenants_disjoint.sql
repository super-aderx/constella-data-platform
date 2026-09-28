-- No order, customer or event id appears under two tenants.
with ids as (
  select
    'order' as kind,
    order_id::text as id,
    tenant_id
  from {{ ref('fct_orders') }}
  union all
  select
    'customer' as kind,
    customer_id::text as id,
    tenant_id
  from {{ ref('dim_customers') }}
  union all
  select
    'event' as kind,
    event_id::text as id,
    tenant_id
  from {{ ref('stg_tps__events') }}
)

select
  kind,
  id,
  count(distinct tenant_id) as tenants
from ids
group by kind, id
having count(distinct tenant_id) > 1
