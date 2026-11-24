{#
  Write every model under models/marts/ to <publish_dir>/<model>.parquet after a run.
  The pipeline workflow uploads that folder to https://data.stefanzhelev.com/messy-orders/.

  Plain COPY instead of dbt-duckdb's `external` materialization: `external` pads
  empty results with an all-NULL row to keep the schema, which is wrong for a
  published file (an empty quarantine must read as 0 rows).
#}
{% macro publish_marts() %}
  {% if execute %}
    {% for node in graph.nodes.values() if node.resource_type == 'model' and 'marts' in node.fqn %}
      {% set rel = adapter.get_relation(database=node.database, schema=node.schema, identifier=node.alias) %}
      {% if rel %}
        {% do run_query("copy " ~ rel ~ " to '" ~ var('publish_dir', 'publish') ~ "/" ~ node.alias ~ ".parquet' (format parquet)") %}
        {% do log("published " ~ node.alias ~ ".parquet", info=true) %}
      {% endif %}
    {% endfor %}
  {% endif %}
{% endmacro %}
