from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta


def print_hello():
    print('hello')


def print_world():
    print('world')


default_args = {
    'owner' : 'airflow',
    'email': ['airflow@airflow.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
}


def generate_dag(investment_type):
    with DAG(
        dag_id = f'print_{investment_type}_value',
        default_args=default_args,
        description=f'This DAG print {investment_type} value',
        schedule_interval='5 5 * * *',
        start_date=days_ago(2),
        tags=['example'],
        catchup=False,
        max_active_runs=1,
    ) as dag:
        print_hello_task = PythonOperator(
            task_id=f'print_{investment_type}_hello',
            python_callable=print_hello,
        ) 
        print_world_task = PythonOperator(
            task_id=f'print_{investment_type}_world',
            python_callable=print_world,
        )
        print_hello_task >> print_world_task
        return dag

investment_types= ['DAG_A', 'DAG_B', 'DAG_C', 'DAG_D']
for _type in investment_types:
    globals()["Dynamic_DAG"+_type] = generate_dag(_type)
