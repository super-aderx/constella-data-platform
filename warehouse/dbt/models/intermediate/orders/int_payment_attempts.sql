-- One row per payment attempt, successful or failed.
select distinct on (tenant_id, payment_id)
  tenant_id,
  payment_id,
  order_id,
  attempt,
  amount_cents,
  failure_code,
  succeeded,
  occurred_at as attempted_at
from {{ ref('stg_tps__payment_events') }}
order by tenant_id, payment_id, occurred_at, event_id
