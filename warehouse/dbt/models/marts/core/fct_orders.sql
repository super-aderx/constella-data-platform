-- Every order, all statuses. segment is set only for paid orders.
with lines as (
  select
    tenant_id,
    order_id,
    count(*)::int as n_lines,
    sum(qty)::int as n_items
  from {{ ref('int_order_items') }}
  group by tenant_id, order_id
)

select
  o.tenant_id,
  o.order_id,
  o.customer_id,
  o.order_day,
  o.status,
  o.placed_at,
  o.paid_at,
  o.cancelled_at,
  o.cancel_reason,
  o.currency,
  o.subtotal_cents,
  o.discount_cents,
  o.total_cents,
  coalesce(l.n_lines, 0) as n_lines,
  coalesce(l.n_items, 0) as n_items,
  s.segment
from {{ ref('int_orders') }} as o
left join lines as l
  on o.tenant_id = l.tenant_id and o.order_id = l.order_id
left join {{ ref('int_order_segments') }} as s
  on o.tenant_id = s.tenant_id and o.order_id = s.order_id
