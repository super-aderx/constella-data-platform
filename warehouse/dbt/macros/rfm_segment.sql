{#- The RFM segment of a customer on `day`, from their paid orders before it:
    first_order_day and last_order_day over all of them, frequency and monetary_cents over the
    365 days before. Rules are checked in order; thresholds come from vars.rfm. -#}
{% macro rfm_segment(day, first_order_day, last_order_day, frequency, monetary_cents) -%}
  {%- set r = var('rfm') -%}
  {%- set recency = '(' ~ day ~ ' - ' ~ last_order_day ~ ')' -%}
  case
    when {{ first_order_day }} is null
      or {{ day }} - {{ first_order_day }} <= {{ var('new_customer_days') }}
      then 'new'
    when {{ recency }} <= {{ r.champion_recency_days }}
      and {{ frequency }} >= {{ r.champion_frequency }}
      and {{ monetary_cents }} >= {{ r.champion_monetary_cents }}
      then 'champions'
    when {{ recency }} <= {{ r.loyal_recency_days }}
      and {{ frequency }} >= {{ r.loyal_frequency }}
      then 'loyal'
    when {{ recency }} <= {{ r.active_recency_days }} then 'potential'
    when {{ recency }} <= {{ r.at_risk_recency_days }}
      and {{ frequency }} >= {{ r.at_risk_frequency }}
      then 'at_risk'
    else 'hibernating'
  end
{%- endmacro %}
