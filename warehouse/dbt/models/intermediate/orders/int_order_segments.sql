-- For every paid order, the customer's RFM state before that day, from their own paid orders:
-- no daily history is stored. Frequency and monetary cover the 365 days before; several orders
-- on one day get the same segment, because every frame ends the day before.
with paid_orders as (
  select
    tenant_id,
    order_id,
    customer_id,
    order_day,
    total_cents
  from {{ ref('int_orders') }}
  where status = 'paid'
),

history as (
  select
    tenant_id,
    order_id,
    customer_id,
    order_day,
    min(order_day) over all_prior as first_order_day,
    max(order_day) over all_prior as last_order_day,
    count(*) over trailing_year as frequency,
    coalesce(sum(total_cents) over trailing_year, 0) as monetary_cents
  from paid_orders
  window
    all_prior as (
      partition by tenant_id, customer_id order by order_day
      range between unbounded preceding and interval '1 day' preceding
    ),
    trailing_year as (
      partition by tenant_id, customer_id order by order_day
      range between interval '365 days' preceding and interval '1 day' preceding
    )
)

select
  tenant_id,
  order_id,
  customer_id,
  order_day,
  first_order_day,
  last_order_day,
  order_day - last_order_day as recency_days,
  frequency::int as frequency,
  monetary_cents::bigint as monetary_cents,
  {{ rfm_segment('order_day', 'first_order_day', 'last_order_day', 'frequency', 'monetary_cents') }}
    as segment
from history
