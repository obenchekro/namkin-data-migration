# data-migration

# Setup
### Prerequisites
First of all, prepare your Hadoop and Spark environment before launching the project.

Install the software on your system and setup the environment variables in the PATH variable.

(Please don't forget to adjust your Java version to Java 8 or Java 11 since that Hadoop and Spark only works flawlessly in those versions.)

* [Python](https://www.python.org/downloads/)
* [Java 8](https://www.oracle.com/technetwork/java/javase/downloads/jre8-downloads-2133155.html)
* [Apache Spark](http://spark.apache.org/downloads.html)
* Optional: [Anaconda](https://www.anaconda.com/distribution/#download-section)

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
All the jobs are restituted inside one main job runner. The ``setup.py`` file is a sort of handmade cronscheduler that runs concurrently all the subprocess defined as arguments passed to the main job runner. 

3. Run this command to enable the job runner to run all the jobs concurrently:
   ```
   python setup.py ./jobs/ods/ods_structure_tables_star_schema.py ./jobs/ods/ods_populate_tables_star_schema.py.py ./jobs/kafka-consumer/kafka_consume_topics_messages.py ./scripts/infrastructure/files-storage/store_files_into_blob_container_azure.py
   ```
