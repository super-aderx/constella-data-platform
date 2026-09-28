-- Each order's status from its events. An order belongs to the local day it was placed.
-- Paid is terminal in TPS, so paid wins over any later cancellation. Status events whose
-- OrderPlaced hasn't arrived yet are left out (assert_orphan_status_events counts them).
with placed as (
  select distinct on (tenant_id, order_id)
    tenant_id,
    order_id,
    customer_id,
    placed_at,
    currency,
    subtotal_cents,
    discount_cents,
    total_cents
  from {{ ref('stg_tps__order_placed') }}
  order by tenant_id, order_id, occurred_at, event_id
),

status_changes as (
  select
    tenant_id,
    order_id,
    min(changed_at) filter (where event_type = 'OrderPaid') as paid_at,
    min(changed_at) filter (where event_type = 'OrderCancelled') as cancelled_at,
    (
      array_agg(reason order by changed_at)
      filter (where event_type = 'OrderCancelled')
    )[1] as cancel_reason
  from {{ ref('stg_tps__order_status_events') }}
  group by tenant_id, order_id
)

select
  p.tenant_id,
  p.order_id,
  p.customer_id,
  p.placed_at,
  {{ local_day('p.placed_at', 't.timezone') }} as order_day,
  s.paid_at,
  s.cancelled_at,
  s.cancel_reason,
  case
    when s.paid_at is not null then 'paid'
    when s.cancelled_at is not null then 'cancelled'
    else 'pending'
  end as status,
  p.currency,
  p.subtotal_cents,
  p.discount_cents,
  p.total_cents
from placed as p
inner join {{ source('platform', 'tenants') }} as t on p.tenant_id = t.tenant_id
left join status_changes as s on p.tenant_id = s.tenant_id and p.order_id = s.order_id
