from datetime import datetime
import logging
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

default_args = {
    "owner": "Kohinoor Biswas",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
}

def log_operator_result(ti, **kwargs):
    logger = logging.getLogger(__name__)
    logger.info("Task '%s' finished with result: %s", ti.task_id, ti.xcom_pull(task_ids=ti.task_id))

with DAG(
    dag_id="instapro",
    default_args=default_args,
    start_date=datetime(2021, 1, 1, 0, 0),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    docker_images = [
        "username/my-image1:latest",
        "username/my-image2:latest",
        "username/my-image3:latest",
    ]

    for i, image in enumerate(docker_images, 1):
        task_id = f"install_docker_image{i}"
        command = f"docker pull {image}"
        task = KubernetesPodOperator(
            task_id=task_id,
            namespace='default',
            image='docker',
            cmds=['docker', 'pull', image],
            name='airflow-install-docker',
            in_cluster=False,
            cluster_context='microk8s',
            config_file='/usr/local/airflow/include/.kube/config',
            is_delete_operator_pod=True,
            get_logs=True,
            dag=dag,
        )

        # Add the logging callback to the task
        task.on_success_callback = log_operator_result
        task.on_failure_callback = log_operator_result

        if i > 1:
            task.set_upstream(prev_task)
        prev_task = task
