-- One row per dbt invocation that changes data (build, run, seed), written by the
-- record_run on-run-end hook. Constella keys its cache on the latest successful finished_at.
create table meta.pipeline_runs (
  run_id uuid primary key,  -- dbt invocation_id
  command text not null,
  started_at timestamptz not null,
  finished_at timestamptz not null,
  status text not null check (status in ('success', 'error'))
);
alter table meta.pipeline_runs owner to dbt_runner;
grant select on meta.pipeline_runs to api_reader;
