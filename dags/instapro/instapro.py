from datetime import datetime
from airflow.operators.empty import EmptyOperator
from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
import yaml

def get_chart_path(chart_name):
    with open('values.yaml', 'r') as f:
        values = yaml.safe_load(f)
        chart_path = values.get('charts', {}).get(chart_name, {}).get('path')
        return chart_path

with DAG(
    dag_id="instapro",
    default_args={
        "owner": "Kohinoor Biswas",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
    },
    start_date=datetime(2021, 1, 1, 0, 0),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    # Task 1: Execute Helm Chart 1
    task1 = KubernetesPodOperator(
        task_id='execute_helm_chart1',
        namespace='default',
        image='helm:latest',
        cmds=['helm', 'install', 'instapro-data-loader', get_chart_path('chart1')],
        dag=dag,
    )

    # Task 2: Execute Helm Chart 2
    task2 = KubernetesPodOperator(
        task_id='execute_helm_chart2',
        namespace='default',
        image='helm:latest',
        cmds=['helm', 'install', 'instapro-data-modeller', get_chart_path('chart2')],
        dag=dag,
    )

    # Task 3: Execute Helm Chart 3
    task3 = KubernetesPodOperator(
        task_id='execute_helm_chart3',
        namespace='default',
        image='helm:latest',
        cmds=['helm', 'install', 'instapro-data-tranformer', get_chart_path('chart3')],
        dag=dag,
    )

    # Define the task dependencies
    task1 >> task2 >> task3
