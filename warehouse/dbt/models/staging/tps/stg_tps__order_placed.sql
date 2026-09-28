select
  tenant_id,
  event_id,
  occurred_at,
  (payload ->> 'order_id')::uuid as order_id,
  (payload ->> 'customer_id')::uuid as customer_id,
  (payload ->> 'placed_at')::timestamptz as placed_at,
  payload ->> 'currency' as currency,
  (payload ->> 'subtotal_cents')::bigint as subtotal_cents,
  (payload ->> 'discount_cents')::bigint as discount_cents,
  (payload ->> 'total_cents')::bigint as total_cents
from {{ ref('stg_tps__events') }}
where
  event_type = 'OrderPlaced'
  and schema_version = 1
