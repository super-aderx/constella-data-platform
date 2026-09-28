-- One row per line of each OrderPlaced event; prices as snapshotted at checkout.
select
  e.tenant_id,
  e.event_id,
  e.occurred_at,
  (e.payload ->> 'order_id')::uuid as order_id,
  items.item ->> 'sku' as sku,
  (items.item ->> 'qty')::int as qty,
  (items.item ->> 'unit_price_cents')::bigint as unit_price_cents,
  (items.item ->> 'line_total_cents')::bigint as line_total_cents
from {{ ref('stg_tps__events') }} as e
cross join lateral jsonb_array_elements(e.payload -> 'items') as items (item)
where
  e.event_type = 'OrderPlaced'
  and e.schema_version = 1
