-- Each customer with their paid-order history and current segment. current_segment applies
-- the RFM rules as of the day after last_complete_day, so the in-progress day doesn't count;
-- it's null for customers who have never had a paid order.
with paid as (
  select
    tenant_id,
    customer_id,
    order_day,
    total_cents
  from {{ ref('fct_orders') }}
  where status = 'paid'
),

lifetime as (
  select
    tenant_id,
    customer_id,
    min(order_day) as first_order_day,
    max(order_day) as last_order_day,
    count(*)::int as paid_orders,
    sum(total_cents)::bigint as lifetime_cents
  from paid
  group by tenant_id, customer_id
),

as_of as (
  select
    p.tenant_id,
    p.customer_id,
    f.last_complete_day + 1 as as_of_day,
    min(p.order_day) as first_order_day,
    max(p.order_day) as last_order_day,
    count(*) filter (where p.order_day >= f.last_complete_day + 1 - 365) as frequency,
    coalesce(
      sum(p.total_cents) filter (where p.order_day >= f.last_complete_day + 1 - 365), 0
    ) as monetary_cents
  from paid as p
  inner join {{ ref('tenant_freshness') }} as f on p.tenant_id = f.tenant_id
  where p.order_day <= f.last_complete_day
  group by p.tenant_id, p.customer_id, f.last_complete_day
)

select
  c.tenant_id,
  c.customer_id,
  c.status,
  c.registered_at,
  l.first_order_day,
  l.last_order_day,
  coalesce(l.paid_orders, 0) as paid_orders,
  coalesce(l.lifetime_cents, 0) as lifetime_cents,
  case
    when a.customer_id is not null
      then {{ rfm_segment('a.as_of_day', 'a.first_order_day', 'a.last_order_day',
                          'a.frequency', 'a.monetary_cents') }}
  end as current_segment
from {{ ref('int_customers') }} as c
left join lifetime as l
  on c.tenant_id = l.tenant_id and c.customer_id = l.customer_id
left join as_of as a
  on c.tenant_id = a.tenant_id and c.customer_id = a.customer_id
