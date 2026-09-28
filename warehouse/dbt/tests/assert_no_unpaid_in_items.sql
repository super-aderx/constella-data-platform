-- fct_order_items, and so every aggregate built from it, holds paid orders only.
select
  i.tenant_id,
  i.order_id,
  o.status
from {{ ref('fct_order_items') }} as i
left join {{ ref('fct_orders') }} as o
  on i.tenant_id = o.tenant_id and i.order_id = o.order_id
where o.status is distinct from 'paid'
