{#- Post-hook on serving views: the tenant filter is applied before any user-supplied
    function or operator sees a row. -#}
{% macro set_security_barrier() -%}
  alter view {{ this }} set (security_barrier = true)
{%- endmacro %}
