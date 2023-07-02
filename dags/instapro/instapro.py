from datetime import datetime
from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.operators.python import PythonOperator
from airflow.operators.dummy_operator import DummyOperator

default_args = {
    "owner": "Kohinoor Biswas",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
}

dag = DAG(
    dag_id="instapro-etl",
    default_args=default_args,
    start_date=datetime(2023, 1, 1),
    schedule_interval="@daily",
    catchup=False,
)

images = [
    {
        "image": "kohinoorthinks/instapro-data-loader:latest",
        "command": ["echo", "Running instapro-data-loader"],
    },
    {
        "image": "kohinoorthinks/instapro-data-modeller:latest",
        "command": ["echo", "Running instapro-data-modeller"],
    },
    {
        "image": "kohinoorthinks/instapro-data-transformer:latest",
        "command": ["echo", "Running instapro-data-transformer"],
    },
]

def print_logs(task, **kwargs):
    logs = kwargs["ti"].xcom_pull(task_ids=task.task_id, key="logs")
    for task_logs in logs:
        print(task_logs)

with dag:
    start_task = DummyOperator(task_id="start_task")

    prev_task = start_task
    for i, image in enumerate(images, 1):
        task_id = f"run_docker_{i}"
        task = KubernetesPodOperator(
            task_id=task_id,
            name=f"run-docker-pod-{i}",
            namespace="airflow",
            image=image["image"],
            image_pull_policy="IfNotPresent",
            cmds=image["command"],
            get_logs=True,
            is_delete_operator_pod=True,
        )

        task_logs = PythonOperator(
            task_id=f"print_logs_{i}",
            python_callable=print_logs,
            op_args=[task],
            provide_context=True,
        )

        prev_task >> task >> task_logs
        prev_task = task_logs

        task_logs.xcom_push(key="logs", value=[task.task_id])

    end_task = DummyOperator(task_id="end_task")
    prev_task >> end_task
