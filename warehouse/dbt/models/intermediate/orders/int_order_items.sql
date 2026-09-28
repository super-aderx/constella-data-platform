-- Lines of each order, from the first OrderPlaced event delivered for it.
with first_placed as (
  select distinct on (tenant_id, order_id)
    tenant_id,
    order_id,
    event_id
  from {{ ref('stg_tps__order_placed') }}
  order by tenant_id, order_id, occurred_at, event_id
)

select
  i.tenant_id,
  i.order_id,
  i.sku,
  i.qty,
  i.unit_price_cents,
  i.line_total_cents
from {{ ref('stg_tps__order_items') }} as i
inner join first_placed as f
  on i.tenant_id = f.tenant_id and i.event_id = f.event_id
