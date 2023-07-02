from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "Kohinoor Biswas",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id="instapro",
    default_args=default_args,
    start_date=datetime(2021, 1, 1, 0, 0),
    schedule_interval="@daily",
    catchup=False,
) as dag:
    helm_charts = [
        "instapro-data-loader",
        "instapro-data-modeller",
        "instapro-data-transformer",
    ]

    for i, chart in enumerate(helm_charts, 1):
        command = f"helm install {chart} /Users/kohinoorbiswas/instapro/charts/{chart}/{chart}-0.1.0.tgz"
        task = BashOperator(
            task_id=f"execute_helm_chart{i}",
            bash_command=command,
            dag=dag,
        )
        if i > 1:
            task.set_upstream(prev_task)
        prev_task = task
