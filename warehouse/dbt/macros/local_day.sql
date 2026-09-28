{#- A timestamptz's local date in an IANA timezone: a "day" everywhere in gold. -#}
{% macro local_day(ts, tz) -%}
  (({{ ts }}) at time zone {{ tz }})::date
{%- endmacro %}
