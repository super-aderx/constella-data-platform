{#- on-run-end: one row in meta.pipeline_runs for each invocation that changes data. -#}
{% macro record_run(results) -%}
  {%- if execute and flags.WHICH in ('build', 'run', 'seed') -%}
    {%- set failed = results | selectattr('status', 'in', ['error', 'fail', 'runtime error']) | list -%}
    insert into meta.pipeline_runs (run_id, command, started_at, finished_at, status)
    values (
      '{{ invocation_id }}',
      '{{ flags.WHICH }}',
      {#- run_started_at is UTC; strftime drops any offset so both naive and aware work. #}
      '{{ run_started_at.strftime("%Y-%m-%d %H:%M:%S.%f") }}'::timestamp at time zone 'utc',
      now(),
      '{{ "error" if failed else "success" }}'
    )
    on conflict (run_id) do nothing
  {%- endif -%}
{%- endmacro %}
