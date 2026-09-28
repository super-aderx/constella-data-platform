select
  tenant_id,
  event_id,
  occurred_at,
  payload ->> 'sku' as sku,
  (payload ->> 'amount_cents')::bigint as amount_cents,
  payload ->> 'currency' as currency,
  (payload ->> 'valid_from')::timestamptz as valid_from
from {{ ref('stg_tps__events') }}
where
  event_type = 'PriceChanged'
  and schema_version = 1
