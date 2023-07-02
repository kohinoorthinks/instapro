from datetime import datetime
from airflow import DAG
from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator

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
        "command": ["echo", "Running Docker image 1"],
    },
    {
        "image": "kohinoorthinks/instapro-data-modeller:latest",
        "command": ["echo", "Running Docker image 2"],
    },
    {
        "image": "kohinoorthinks/instapro-data-transformer:latest",
        "command": ["echo", "Running Docker image 3"],
    },
]

prev_task = None
for i, image in enumerate(images, 1):
    task = KubernetesPodOperator(
        task_id=f"run_docker_{i}",
        name=f"run-docker-pod-{i}",
        namespace="airflow",
        image=image["image"],
        image_pull_policy="IfNotPresent",
        cmds=image["command"],
        get_logs=True,
        is_delete_operator_pod=False,
        dag=dag,
    )

    if prev_task:
        task.set_upstream(prev_task)
    prev_task = task

task
