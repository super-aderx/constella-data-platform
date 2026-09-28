{{ config(severity='warn') }}

-- Status events whose OrderPlaced hasn't arrived (yet). int_orders leaves them out until it does.
select
  s.tenant_id,
  s.order_id,
  s.event_type
from {{ ref('stg_tps__order_status_events') }} as s
left join {{ ref('int_orders') }} as o
  on s.tenant_id = o.tenant_id and s.order_id = o.order_id
where o.order_id is null
