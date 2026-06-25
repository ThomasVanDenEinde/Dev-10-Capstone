from airflow.sdk import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

default_args = {
   'owner': 'airflow',
   'start_date': datetime(2026, 1, 1),
}

with DAG('capstone_dag', default_args=default_args, schedule='@daily') as capstone_dag:
    create_schema = SQLExecuteQueryOperator(
    task_id="instantiate_fresh_tables",
    sql="capstone.sql",
    conn_id="pg_conn",
    )

    submit_etl = SparkSubmitOperator(
    application="/opt/airflow/work-dir/etl.py",
    task_id="etl"
   )

    create_schema >> submit_etl

