{#- Like relationships, but the parent must be in the same tenant: keys such as SKUs are only
    unique within a tenant. -#}
{% test tenant_relationships(model, column_name, to, field) %}
  select
    child.tenant_id,
    child.{{ column_name }}
  from {{ model }} as child
  left join {{ to }} as parent
    on
      child.tenant_id = parent.tenant_id
      and child.{{ column_name }} = parent.{{ field }}
  where
    child.{{ column_name }} is not null
    and parent.{{ field }} is null
{% endtest %}
