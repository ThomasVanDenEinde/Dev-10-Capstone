import pendulum

from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sdk import dag, task


# Run a board game dag that creates the necessary database schema for the board game ETL process. 
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
    board_game_schema = SQLExecuteQueryOperator(
        task_id="instantiate_fresh_tables",
        sql="capstone.sql",
        conn_id="pg_conn",
    )

    board_game_schema

instantiate_fresh_tables_dag()