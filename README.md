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

# Design a data pipeline that includes the following steps:
## a.	Data Ingestion
## i.	Load the dataset into the database
## ii.	You can choose to create a Python script to do some initial transformations before loading it
## iii.	Document the deployment process and any configurations needed for data ingestion.

The solution uses an ELT approach to load CSV file into database , models the data , and then creates transformed availability snapshot for the data.
### Disclaimier :  
The airflow set up is using solution by Guido Kosloff Gancedo available at (https://github.com/guidok91/airflow)

### Deployemnt
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
  host: airflow-postgresql
  port: 5432
  database: postgres
  username: postgres
  postgresPassword: postgres

#### Configuration
If you need to customize [Airflow configuration](https://airflow.apache.org/docs/apache-airflow/stable/configurations-ref.html) you can edit the `config` section in [values.yaml](k8s/values.yaml).

Also environment variables can be added in the `env` section (they will be present in all the pods). 

#### DAG deployment
DAGs are deployed via GitSync.

GitSync acts as a side car container alongside the other Airflow pods, synchronising the `dags/` folder in the pods with the DAGs located in a Git repo of your choice (in this case https://github.com/kohinoorthinks/instapro.git).

#### ELT image configuration
While no changes will be needed if airflow with postgres is configured as mnetioned above, cutome db creds can be configured for respective docker images.
From airflow directory
`cd ..`
`cd data_loader`
`nano values.yaml`
Make changes as needed. dont change if using project defaults
build docker image, images are built for apple silicon, so if running on different architecture this step is mandatory. 
`docker build -t instapro-data-loader .`
`docker tag instapro-data-loader kohinoorthinks/instapro-data-loader`
`docker push kohinoorthinks/instapro-data-loader:latest`
`cd ..`
`cd data_modeller`
`nano values.yaml`
`docker build -t instapro-data-modeller .`
`docker tag instapro-data-modeller kohinoorthinks/instapro-data-modeller`
`docker push kohinoorthinks/instapro-data-modeller:latest`
`cd ..`
`cd data_transformer`
`nano values.yaml`
`docker build -t instapro-data-transformer .`
`docker tag instapro-data-transformer kohinoorthinks/instapro-data-transformer`
`docker push kohinoorthinks/instapro-data-transformer:latest`




