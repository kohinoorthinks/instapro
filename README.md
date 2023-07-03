# instapro

# 1.Choose a relational database (e.g., PostgreSQL, MySQL) and provide a justification for your choice, considering factors such as scalability, performance, and community support

For the given tasks, I recommend using PostgreSQL as the relational database. Here's the justification for choosing PostgreSQL:

1. Scalability: PostgreSQL is known for its scalability capabilities. It supports horizontal scalability through features like table partitioning and parallel query execution. It also offers built-in replication and clustering options for high availability and load balancing.

2. Performance: PostgreSQL has a reputation for delivering excellent performance, especially when it comes to complex queries and large datasets. It has advanced optimization techniques, such as cost-based query optimization, multi-version concurrency control (MVCC), and support for indexing and advanced data types. These features contribute to efficient query execution and faster response times.

3. Community Support: PostgreSQL has a large and active open-source community that provides ongoing support, bug fixes, and feature enhancements. It is widely adopted and has a strong ecosystem of third-party tools, libraries, and extensions. The community support ensures the stability, security, and continuous improvement of the database.

4. Advanced Features: PostgreSQL offers a rich set of features that make it suitable for a wide range of use cases. It supports complex data types, JSON and spatial data, full-text search, and advanced analytics through extensions like PostGIS and pgcrypto. It also provides support for stored procedures, triggers, and views, enabling data transformation and manipulation within the database.

5. Reliability and Durability: PostgreSQL is known for its data integrity and durability. It implements the ACID (Atomicity, Consistency, Isolation, Durability) principles, ensuring that transactions are processed reliably and that data remains consistent even in the event of failures or crashes.

6. Compatibility: PostgreSQL is ANSI SQL compliant, which means it follows the SQL standards. It also supports various programming languages and frameworks, making it easy to integrate with existing systems and applications.

Considering these factors, PostgreSQL is a great choice for building a data pipeline that requires scalability, performance, and community support. Its advanced features, reliability, and compatibility make it well-suited for handling large datasets and enabling efficient querying.

# Data Pipeline Design

This document outlines the design of a data pipeline that includes data ingestion, data transformation and modeling, and orchestration steps.

## Data Ingestion

The data ingestion process involves loading the dataset into the database. It can include initial transformations using a Python script before loading. Here are the steps involved:

1. **Data Loading**: Load the dataset into the database. Specify the necessary configuration settings such as the database connection details, target schema, and table.

2. **Initial Transformations**: If required, create a Python script to perform initial transformations on the data before loading it into the database. This script can handle tasks such as data cleansing, formatting, or filtering.

3. **Deployment Process**: Document the deployment process for the data ingestion pipeline. Specify the necessary configurations, such as the database credentials, dataset location, and any additional dependencies or tools required.

## Data Transformation and Modeling

The data transformation and modeling step involves transforming the data in the database using SQL, dbt, or Python. It also includes applying Dimensional Modeling principles to design the schema, including fact and dimension tables. Here are the steps involved:

1. **Data Transformation**: Use SQL, dbt (data build tool), or Python scripts to perform data transformations in the database. These transformations can include aggregations, calculations, data joins, or any other required operations.

2. **Dimensional Modeling**: Apply Dimensional Modeling principles to design the schema. This involves identifying fact and dimension tables, defining relationships between them, and establishing appropriate indexes, primary keys, and foreign key relationships.

3. **Optimizations**: Optimize the database schema and query performance by defining indexes, primary keys, and foreign key relationships. These optimizations can enhance the efficiency and speed of data retrieval and analysis.

## Orchestration

The orchestration step involves using Airflow to create DAGs (Directed Acyclic Graphs) that orchestrate the workflows of the data pipeline. For deployment, you can create a custom Helm chart or use the official Helm chart to deploy the pipeline on a local Kubernetes cluster (e.g., microk8s, minikube). Here are the steps involved:

1. **Airflow DAGs**: Use Airflow to create DAGs that define the workflow of the data pipeline. These DAGs should specify the sequence of tasks, dependencies between them, and any required parameters or configurations.

2. **Deployment with Helm**: For deployment, you can create your own Helm chart or use the official Helm chart. Helm is a package manager for Kubernetes that simplifies the deployment process. Document the deployment process using Helm, including any necessary configurations, such as the number of replicas, resource limits, and persistent storage requirements.

3. **Helm Chart Values**: Write YAML files for the Helm chart values. These files specify the configuration settings for the data pipeline deployment, such as database connection details, credentials, environment variables, and any other necessary parameters.

## Deployment Process

The deployment process involves setting up the data pipeline and any necessary configurations or optimizations. Here are the steps involved:

1. **Data Ingestion**: Follow the documented deployment process for data ingestion, including the necessary configurations and optimizations.

2. **Data Transformation and Modeling**: Execute the data transformation and modeling steps, using the specified tools and following the documented deployment process. Apply any optimizations to enhance query performance.

3. **Orchestration**: Deploy the data pipeline using Airflow and Helm. Follow the documented deployment process for setting up Airflow DAGs and Helm chart values. Ensure all necessary configurations and environment variables are correctly defined.


The solution uses an ELT approach to load CSV file into database , models the data , and then creates transformed availability snapshot for the data.
### Disclaimer/Credits :  
The airflow set up is using solution by Guido Kosloff Gancedo available at (https://github.com/guidok91/airflow)

# Deployment
## Requirements
[Kind](https://kind.sigs.k8s.io/), [Docker](https://www.docker.com/) and [Helm](https://helm.sh/) for local Kubernetes cluster.

#### clone repository
`git clone https://github.com/kohinoorthinks/instapro.git`

`cd instapro`

#### Spin up airflow, postgres , kubernetes
`cd airflow`

#### Instructions
The repo includes a `Makefile`. You can run `make help` to see usage.

Basic setup:
- Run `make k8s-cluster-up` to spin up local Kubernetes cluster with Kind.
- Run `make airflow-k8s-add-helm-chart` to add the official Airflow Helm chart to the local repo.
- Run `make airflow-k8s-create-namespace` to create a namespace for the Airflow deployment.
- Run `make airflow-k8s-up` to deploy Airflow on the local Kubernetes cluster.
- On a separate terminal, run `make airflow-webserver-port-forward` to be able to access the Airflow webserver on http://localhost:8080.

The credentials for the webserver are admin/admin.
- On a separate terminal, run `make pgadmin-port-forward` to be able to access the pgadmin webserver on http://localhost:9090.

The credentials for the pgadmin are admin@admin.com/mypwd

- Connect to postgresdb using pgadmin 
  - host: airflow-postgresql
  - port: 5432
  - database: postgres
  - username: postgres
  - postgresPassword: postgres

#### Configuration
If you need to customize [Airflow configuration](https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html) you can edit the `config` section in [values.yaml](k8s/values.yaml).

Also environment variables can be added in the `env` section (they will be present in all the pods). 

#### DAG deployment
DAGs are deployed via GitSync.

GitSync acts as a side car container alongside the other Airflow pods, synchronising the `dags/` folder in the pods with the DAGs located in a Git repo of your choice (in this case https://github.com/kohinoorthinks/instapro.git).

#### ELT image configuration
While no changes will be needed if airflow with postgres is configured as mentioned above, cutom db credentials can be configured for respective docker images.
From airflow directory
- `cd ..`
- `cd data_loader`
- `nano values.yaml`
Make changes as needed. dont change if using project defaults
build docker image, images are built for apple silicon, so if running on different architecture this step is mandatory. 
- `docker build -t instapro-data-loader .`
- `docker tag instapro-data-loader kohinoorthinks/instapro-data-loader`
- `docker push kohinoorthinks/instapro-data-loader:latest`
- `cd ..`
- `cd data_modeller`
- `nano values.yaml`
- `docker build -t instapro-data-modeller .`
- `docker tag instapro-data-modeller kohinoorthinks/instapro-data-modeller`
- `docker push kohinoorthinks/instapro-data-modeller:latest`
- `cd ..`
- `cd data_transformer`
- `nano values.yaml`
- `docker build -t instapro-data-transformer .`
- `docker tag instapro-data-transformer kohinoorthinks/ instapro-data-transformer`
- `docker push kohinoorthinks/instapro-data-transformer:latest`

##### Execute DAG
- Login to airflow at `http://localhost:8080`
- username:admin
- password:admin

execute / manually trigger dag : instapro-etl

Once Dag Completes execution
- Login to pg admin : `http://localhost:9090`
- username: admin@admin.com
- password: mypwd

In postgres db there should be schema: instapro
Verify output:
`select * from instapro.availability_snapshot`

#### helm charts (optioal)
- helm charts for the etl ptocess can also be installed if not executing the dag
- `cd project_root/charts/instapro-data-loader`
- `helm install instapro-data-loader ./instapro-data-loader-0.1.0.tgz -n airflow`
- `cd project_root/charts/instapro-data-modeller`
- `helm install instapro-data-modeller ./instapro-data-modeller-0.1.0.tgz -n airflow`
- `cd project_root/charts/instapro-data-transformer`
- `helm install instapro-data-transformer ./instapro-data-transformer-0.1.0.tgz -n airflow`

## Data Model

The data model consists of four tables: `service_dim`, `event_dim`, `professional_dim`, and `event_fact`. These tables are designed to store the data in a way that optimizes readability and ease of querying for product analysts.

### 1. `service_dim` Table:
This table stores information about different services offered. It has the following columns:
- `id`: A unique identifier for each service (auto-incremented).
- `service_id`: The ID of the service.
- `service_name_nl`: The name of the service in Dutch.
- `service_name_en`: The name of the service in English.
- `lead_fee`: The lead fee for the service (in decimal format).

### 2. `event_dim` Table:
This table stores information about different types of events. It has the following columns:
- `event_type_id`: A unique identifier for each event type (auto-incremented).
- `event_type`: The type of the event.

### 3. `professional_dim` Table:
This table stores information about professionals. It has the following columns:
- `professional_id`: A unique identifier for each professional (auto-incremented).
- `professional_id_anonymized`: Anonymized ID of the professional.

### 4. `event_fact` Table:
This table stores information about events. It has the following columns:
- `event_fact_id`: A unique identifier for each event (auto-incremented).
- `event_id`: The ID of the event.
- `event_type`: The type of the event.
- `professional_id_anonymized`: Anonymized ID of the professional associated with the event.
- `created_at`: The date and time when the event occurred.
- `service_id`: The ID of the service associated with the event.

The tables are connected through foreign key relationships to ensure data integrity and enable efficient querying and analysis.

### Question 2
#### Create a single DAG file that orchestrates the data pipeline, from loading until creating the final tables. 
#### Dynamic DAG generation:
-	A DAG factory that generates the pipeline code for daily, weekly, and monthly schedule
#### YAML Config:
-	Use Kubernetes ConfigMaps and Secrets for environment variables needed for the DAG
-	Add them in the Helm chart so it can be included during the deployment of the Airflow instance
#### Question 3
Create an availability_snapshot table that would store the amount of active professionals per day (reminder: an active professional is a professional who is “able to propose”).

In project root
- `cd dags\instapro`
- review instapro.py for reference.

On execution of the dag from airflow ui logs for the dag can be seen under
project_root/airflow/data/dag_id=instapro-etl

Sample output is available at
project_root/output/availability_snapshot.csv

#### Question 4
#### Design a CI/CD pipeline in Github/Gitlab in YAML, make sure it does the following:
-	Runs the test suite for unit, integration, and end-to-end tests
-	Builds the tables of the data model and make sure that the schema and data tests pass
-	Cleanup of resources once CI/CD pipeline finished running

The CI/CD pipeline can be found at:
- project_root/.github/workflows/ci-cd.yml
#### CI/CD Pipeline Configuration

This CI/CD pipeline is designed to automate the build, testing, and deployment processes for the project. It consists of three jobs: `build-and-test`, `build-database`, and `cleanup`.

#### Build and Test

The `build-and-test` job is responsible for building and testing the application. Here are the steps involved:

1. **Checkout Repository**: This step checks out the source code repository.

2. **Set Up Python**: This step sets up the Python environment using the specified version.

3. **Install Dependencies**: This step installs the project dependencies specified in the `requirements.txt` file.

4. **Run Unit Tests**: This step runs the unit tests for the application.

5. **Run Integration Tests**: You can add commands in this step to run integration tests.

6. **Run End-to-End Tests**: You can add commands in this step to run end-to-end tests.

## Build Database

The `build-database` job handles tasks related to the database. Here are the steps involved:

1. **Checkout Repository**: This step checks out the source code repository.

2. **Set Up Python**: This step sets up the Python environment using the specified version.

3. **Install Dependencies**: This step installs the project dependencies specified in the `requirements.txt` file.

4. **Apply Database Migrations**: This step applies any pending database migrations using Django's migration framework.

5. **Run Schema and Data Tests**: You need to add commands in this step to run tests that validate the database schema and data integrity.

#### Cleanup

The `cleanup` job performs necessary cleanup tasks after the build and database jobs. Here are the steps involved:

1. **Checkout Repository**: This step checks out the source code repository.

2. **Clean Up Resources**: Add commands in this step to clean up any temporary or test resources created during the CI/CD process.

#### Workflow

The pipeline is triggered on each push to the `main` branch. The jobs are executed sequentially: `build-and-test` -> `build-database` -> `cleanup`. The `cleanup` job depends on the completion of the previous two jobs.













