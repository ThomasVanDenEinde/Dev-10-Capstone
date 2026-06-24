from airflow.sdk import DAG, dag
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime
from airflow.operators.bash import BashOperator
import pendulum
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

@dag(
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["instantiate_fresh_tables", "sql"],
)
def instantiate_fresh_tables_dag():
    """
    The DAG consists of a single task:
    1. `board_game_schema`: Executes a SQL script to create the necessary database schema.
    """
    capstone_schema = SQLExecuteQueryOperator(
        task_id="instantiate_fresh_tables",
        sql="capstone.sql",
        conn_id="pg_conn",
    )

    capstone_schema

instantiate_fresh_tables_dag()

default_args = {
   'owner': 'airflow',
   'start_date': datetime(2026, 1, 1),
   'retries': 1,
}
with DAG('executing_example_etl_dag', default_args=default_args, schedule='@daily') as dag:
   submit_job = SparkSubmitOperator(
       application="/opt/airflow/work-dir/etl.py",
       task_id="etl"
   )


instantiate_fresh_tables >> etl