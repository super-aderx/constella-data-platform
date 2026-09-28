-- Lines of paid orders only, with the order's day and segment.
select
  i.tenant_id,
  i.order_id,
  i.sku,
  o.customer_id,
  o.order_day,
  o.segment,
  i.qty,
  i.unit_price_cents,
  i.line_total_cents
from {{ ref('int_order_items') }} as i
inner join {{ ref('fct_orders') }} as o
  on i.tenant_id = o.tenant_id and i.order_id = o.order_id
where o.status = 'paid'
