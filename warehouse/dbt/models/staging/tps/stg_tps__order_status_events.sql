-- Terminal order transitions: OrderPaid and OrderCancelled.
select
  tenant_id,
  event_id,
  event_type,
  occurred_at,
  (payload ->> 'order_id')::uuid as order_id,
  coalesce(payload ->> 'paid_at', payload ->> 'cancelled_at')::timestamptz as changed_at,
  payload ->> 'reason' as reason
from {{ ref('stg_tps__events') }}
where
  event_type in ('OrderPaid', 'OrderCancelled')
  and schema_version = 1
