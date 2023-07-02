from datetime import datetime
from airflow.operators.empty import EmptyOperator
from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
import yaml


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
        cmds=['helm', 'install', 'instapro-data-loader', '~/instapro/charts/instapro-data-loader/instapro-data-loader-0.1.0.tgz'],
        dag=dag,
    )

    # Task 2: Execute Helm Chart 2
    task2 = KubernetesPodOperator(
        task_id='execute_helm_chart2',
        namespace='default',
        image='helm:latest',
        cmds=['helm', 'install', 'instapro-data-modeller', '~/instapro/charts/instapro-data-modeller/instapro-data-modeller-0.1.0.tgz'],
        dag=dag,
    )

    # Task 3: Execute Helm Chart 3
    task3 = KubernetesPodOperator(
        task_id='execute_helm_chart3',
        namespace='default',
        image='helm:latest',
        cmds=['helm', 'install', 'instapro-data-tranformer', '~/instapro/charts/instapro-data-transformer/instapro-data-transformer-0.1.0.tgz'],
        dag=dag,
    )

    # Define the task dependencies
    task1 >> task2 >> task3
