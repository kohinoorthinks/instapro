from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "Kohinoor Biswas",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
}

dag = DAG(
    dag_id="download_helm_chart",
    default_args=default_args,
    start_date=datetime(2021, 1, 1, 0, 0),
    schedule_interval="@daily",
    catchup=False,
)

# Command to download Helm chart from GitHub and add it to the local repository
download_command = """
mkdir -p ~/instapro_charts
cd ~/instapro_charts
git clone https://github.com/kohinoorthinks/instapro.git
cd instapro/charts/instapro-data-loader
helm repo index .
cd ~/instapro_charts/instapro-data-modeller
helm repo index .
cd ~/instapro_charts/instapro-data-tarnsformer/instapro-data-tarnsformer
helm repo index .
"""

# Task to download and add Helm chart to local repository
download_task = BashOperator(
    task_id="download_chart",
    bash_command=download_command,
    dag=dag,
)

# Set the task dependencies
download_task

