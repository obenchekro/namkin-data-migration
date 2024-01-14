# data-migration

## Setup
### Prerequisites
First of all, prepare your Hadoop and Spark environment before launching the project.

Install the software on your system and setup the environment variables in the PATH variable.

(Please don't forget to adjust your Java version to Java 8 or Java 11 since that Hadoop and Spark only works flawlessly in those versions.)

* [Python](https://www.python.org/downloads/)
* [Java 8](https://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html)
* [Apache Spark](http://spark.apache.org/downloads.html)

If you're familiar with Linux, you will have to export for example these environment variables:
```
export JAVA_HOME=$(/usr/libexec/java_home)
export SPARK_HOME=~/spark-3.3.2-bin-hadoop3.3.4
export PATH=$SPARK_HOME/bin:$PATH
export PYSPARK_PYTHON=python3
```

Hadoop and Spark are quite tedious to configure and some flaws might come insidiously if one dependency is incompatible.
To resolve this kind of dependency conflict, working on a Databricks notebook might come handy in that case. 

Using Databricks cluster makes the dependencies easier to integrate and to unify.
Here's a link to try out the community edition even though some functionalities are limited: [Databricks Community Edition](https://docs.databricks.com/en/getting-started/community-edition.html)

You'll also need a Azure account to ingest the files version history located in the data folder on azure container: [Microsoft Azure](https://portal.azure.com/)

### Database configuration
Data storage solution is based on SQL Server so you'll have to follow few steps to start off the configuration and the basic database initialization:
1. Download **SQL Server**:
   - Visit the [SQL Server download page](https://www.microsoft.com/en-us/sql-server/sql-server-downloads).
   - Select the appropriate edition of SQL Server (Express edition is free and sufficient for basic use) then launch the wizard installation.

2. Download **SSMS**:
   - Go to the [SSMS download page](https://docs.microsoft.com/en-us/sql/ssms/download-sql-server-management-studio-ssms).
   - Click the download link for the latest SSMS version and follow the installation steps.

After setting up SSMS and the database service, you'll have to run the following commands in order to create the ODS and DWH database through Windows Authentification.

3. Run the following command in Powershell:
```
sqlcmd -S <your-local-machine> -E -i "./scripts/infrastructure/dwh/create_dwh_production_db.sql"
```

You'll also need to create an administrator role and grant to this user all the read and write operations in all the databases.

3. Run the following command in Powershell:
```
sqlcmd -S <your-local-machine> -E -i "./scripts/infrastructure/dwh/init_login_and_owner.sql
```
### Launching the project

``pyproject.toml`` file is dedicated to encompass all the right packages version ensuring compatibility. This package file is generated by **poetry** library.

1. Install **poetry** in the project:
```
pip install poetry
```
2. Run this command in order to install all the dependencies annotated in the ``pyproject.toml``
```
poetry install --no-root
```
All the jobs are restituted inside one main job runner. The ``setup.py`` file is a sort of handmade cron scheduler that runs concurrently all the subprocess defined as arguments passed to the main job runner. 

3. Run this command to enable the job runner to run all the jobs concurrently:
```
python setup.py ./jobs/ods/ods_structure_tables_star_schema.py ./jobs/ods/ods_populate_tables_star_schema.py.py ./jobs/kafka-consumer/kafka_consume_topics_messages.py ./scripts/infrastructure/files-storage/store_files_into_blob_container_azure.py
```
## Data Migration Architecture
<img width="100%" src="https://ibb.co/yg2ypFw">
