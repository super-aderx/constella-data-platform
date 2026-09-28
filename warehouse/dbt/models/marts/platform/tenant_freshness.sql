-- How far each tenant's data goes. A local day is complete once its end is at least
-- completion_grace_minutes behind the newest event (an order placed before midnight can be
-- paid up to 15 minutes later).
with events as (
  select
    tenant_id,
    max(occurred_at) as last_event_at
  from {{ ref('stg_tps__events') }}
  group by tenant_id
),

orders as (
  select
    tenant_id,
    min(order_day) as first_day
  from {{ ref('fct_orders') }}
  where status = 'paid'
  group by tenant_id
)

select
  t.tenant_id,
  o.first_day,
  e.last_event_at,
  (
    (e.last_event_at at time zone t.timezone)
    - interval '{{ var("completion_grace_minutes") }} minutes'
  )::date - 1 as last_complete_day,
  now() as refreshed_at
from {{ source('platform', 'tenants') }} as t
inner join events as e on t.tenant_id = e.tenant_id
left join orders as o on t.tenant_id = o.tenant_id
