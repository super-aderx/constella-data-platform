-- platform and bronze belong to the admin; dbt owns everything it builds.
create schema platform;
create schema bronze;
create schema silver authorization dbt_runner;
create schema gold authorization dbt_runner;
create schema serving authorization dbt_runner;
create schema meta authorization dbt_runner;

grant usage on schema platform to loader, dbt_runner, api_reader;
grant usage on schema bronze to loader, dbt_runner;
grant usage on schema serving, meta to api_reader;

-- Tables the admin creates later in these schemas get the same grants.
alter default privileges in schema platform
grant select on tables to loader, dbt_runner, api_reader;
alter default privileges in schema bronze grant select on tables to dbt_runner;
alter default privileges in schema bronze grant insert on tables to loader;
