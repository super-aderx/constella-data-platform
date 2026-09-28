-- One row per payment attempt, successful or not.
select
  tenant_id,
  event_id,
  occurred_at,
  (payload ->> 'payment_id')::uuid as payment_id,
  (payload ->> 'order_id')::uuid as order_id,
  (payload ->> 'attempt')::int as attempt,
  (payload ->> 'amount_cents')::bigint as amount_cents,
  payload ->> 'failure_code' as failure_code,
  event_type = 'PaymentSucceeded' as succeeded
from {{ ref('stg_tps__events') }}
where
  event_type in ('PaymentSucceeded', 'PaymentFailed')
  and schema_version = 1
