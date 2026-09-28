{#- The session's tenant. The API sets it per transaction with
    set_config('app.tenant_id', <uuid>, true); unset, it's null and tenant-scoped views are empty. -#}
{% macro current_tenant() -%}
  nullif(current_setting('app.tenant_id', true), '')::uuid
{%- endmacro %}
