select
  tenant_id,
  event_id,
  event_type,
  occurred_at,
  (payload ->> 'customer_id')::uuid as customer_id,
  payload ->> 'status' as status,
  (payload ->> 'registered_at')::timestamptz as registered_at
from {{ ref('stg_tps__events') }}
where
  event_type in ('CustomerRegistered', 'CustomerUpdated')
  and schema_version = 1
