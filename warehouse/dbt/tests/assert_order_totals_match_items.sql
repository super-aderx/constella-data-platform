-- subtotal_cents = sum of line_total_cents, for every order of every status.
select
  o.tenant_id,
  o.order_id,
  o.subtotal_cents,
  sum(i.line_total_cents) as lines_cents
from {{ ref('fct_orders') }} as o
left join {{ ref('int_order_items') }} as i
  on o.tenant_id = i.tenant_id and o.order_id = i.order_id
group by o.tenant_id, o.order_id, o.subtotal_cents
having o.subtotal_cents is distinct from sum(i.line_total_cents)
