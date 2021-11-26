from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.utils.dates import days_ago
from airflow.sensors.external_task_sensor import ExternalTaskMarker, ExternalTaskSensor

default_args={
        "owner": "airflow",
        "start_date": datetime(2021,11, 19),
        }
with DAG(
dag_id="watch_print_time_to_txt",
default_args=default_args,
schedule_interval='35 20 * * *',
#concurrency=1,
#max_active_runs=1,
tags=['example1'],
 ) as child_dag:
# [START howto_operator_external_task_sensor]
     child_task1 = ExternalTaskSensor(
     task_id="watch_print_time_to_txt",
     external_dag_id="test_dag",
     external_task_id="print_time_to_text_task",
    # timeout=600,
    # allowed_states=['success'],
    # failed_states=['failed', 'skipped'],
     execution_delta=timedelta(minutes=5)   # 观察 1 天前的 dag
    # mode= "reschedule",
     )

 # [END howto_operator_external_task_sensor]
     t1 = BashOperator(
        task_id='print_date',
        bash_command='cat /opt/airflow/logs/date.txt',
        dag = child_dag
    )

child_task1 >> t1
