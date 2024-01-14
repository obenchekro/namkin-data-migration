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
Data storage solution is based on SQL Server so you'll have to follow a few steps to start off the configuration and the basic database initialization:
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
![alt text](https://i.ibb.co/BTkZG2X/NAMKIN-DATA-ARCHITECTURE.jpg)
### Global Pipeline
The global pipeline regroups all the PyODBC/PySpark jobs by formatting the DDL scripts of the ODS tables and executing. This workflow is followed by populating the tables using several transformation, leverage, joins and filters on the relevant fields in the right records format to be finally inserted successfully in the dedicated ODS tables.

On the other side, a Kafka consumer is exposed on a port in order to stream the messages from numerous partitions of the topics that mostly gather the transactional data from the targetted microservice API. A Kafka processor is then triggered depending on the topic message consumed, feeding the ODS tables.

The Kafka processor is quite complex and intricate. Regarding the method HTTP provided, it'll perform a specific data leverage on the pinpointed topic message.

The final step is to run a ready-to-use scripts to truncate the DWH table affected and bulk all the records from the updated ODS table. This'll guarantee that data quality is as fresh as it was before.

### Logging and Error Handling in jobs
Logs and exceptions are encapsulated on files setting the level of the message, the hierarchy of the subjob, the datetime of the event and the information provided. You'll find the files in the ``logs`` folder.

Here's an example of the logging file for the ``ods_populate_tables_star_schema.log``:
```
2024-01-01 18:45:10,512 - root - INFO - Spark session created successfully.
2024-01-01 18:45:10,512 - root - INFO - Starting to convert machine-1-0.csv CSV file to Parquet format.
2024-01-01 18:45:10,718 - root - INFO - Converted machine-1-0.csv to Parquet format successfully.
2024-01-01 18:45:10,718 - root - INFO - Starting to convert machine-10-0.csv CSV file to Parquet format.
2024-01-01 18:45:10,872 - root - INFO - Converted machine-10-0.csv to Parquet format successfully.
2024-01-01 18:45:10,873 - root - INFO - Starting to convert machine-11-0.csv CSV file to Parquet format.
2024-01-01 18:45:11,032 - root - INFO - Converted machine-11-0.csv to Parquet format successfully.
2024-01-01 18:45:11,033 - root - INFO - Starting to convert machine-12-0.csv CSV file to Parquet format.
2024-01-01 18:45:11,213 - root - INFO - Converted machine-12-0.csv to Parquet format successfully.
2024-01-01 18:45:11,213 - root - INFO - Starting to convert machine-13-0.csv CSV file to Parquet format.
2024-01-01 18:45:11,370 - root - INFO - Converted machine-13-0.csv to Parquet format successfully.
2024-01-01 18:45:11,370 - root - INFO - Starting to convert machine-14-0.csv CSV file to Parquet format.
2024-01-01 18:45:11,525 - root - INFO - Converted machine-14-0.csv to Parquet format successfully.
2024-01-01 18:45:11,525 - root - INFO - Starting to convert machine-15-0.csv CSV file to Parquet format.
2024-01-01 18:45:11,683 - root - INFO - Converted machine-15-0.csv to Parquet format successfully.
2024-01-01 18:45:11,683 - root - INFO - Starting to convert machine-16-0.csv CSV file to Parquet format.
2024-01-01 18:45:11,842 - root - INFO - Converted machine-16-0.csv to Parquet format successfully.
2024-01-01 18:45:11,843 - root - INFO - Starting to convert machine-17-0.csv CSV file to Parquet format.
2024-01-01 18:45:11,998 - root - INFO - Converted machine-17-0.csv to Parquet format successfully.
2024-01-01 18:45:11,999 - root - INFO - Starting to convert machine-18-0.csv CSV file to Parquet format.
2024-01-01 18:45:12,159 - root - INFO - Converted machine-18-0.csv to Parquet format successfully.
2024-01-01 18:45:12,159 - root - INFO - Starting to convert machine-19-0.csv CSV file to Parquet format.
2024-01-01 18:45:12,307 - root - INFO - Converted machine-19-0.csv to Parquet format successfully.
2024-01-01 18:45:12,307 - root - INFO - Starting to convert machine-2-0.csv CSV file to Parquet format.
2024-01-01 18:45:12,464 - root - INFO - Converted machine-2-0.csv to Parquet format successfully.
2024-01-01 18:45:12,464 - root - INFO - Starting to convert machine-20-0.csv CSV file to Parquet format.
2024-01-01 18:45:12,625 - root - INFO - Converted machine-20-0.csv to Parquet format successfully.
2024-01-01 18:45:12,625 - root - INFO - Starting to convert machine-21-0.csv CSV file to Parquet format.
2024-01-01 18:45:12,772 - root - INFO - Converted machine-21-0.csv to Parquet format successfully.
2024-01-01 18:45:12,772 - root - INFO - Starting to convert machine-22-0.csv CSV file to Parquet format.
2024-01-01 18:45:12,927 - root - INFO - Converted machine-22-0.csv to Parquet format successfully.
2024-01-01 18:45:12,927 - root - INFO - Starting to convert machine-23-0.csv CSV file to Parquet format.
2024-01-01 18:45:13,084 - root - INFO - Converted machine-23-0.csv to Parquet format successfully.
2024-01-01 18:45:13,084 - root - INFO - Starting to convert machine-24-0.csv CSV file to Parquet format.
2024-01-01 18:45:13,240 - root - INFO - Converted machine-24-0.csv to Parquet format successfully.
2024-01-01 18:45:13,240 - root - INFO - Starting to convert machine-25-0.csv CSV file to Parquet format.
2024-01-01 18:45:13,394 - root - INFO - Converted machine-25-0.csv to Parquet format successfully.
2024-01-01 18:45:13,394 - root - INFO - Starting to convert machine-26-0.csv CSV file to Parquet format.
2024-01-01 18:45:13,546 - root - INFO - Converted machine-26-0.csv to Parquet format successfully.
2024-01-01 18:45:13,546 - root - INFO - Starting to convert machine-27-0.csv CSV file to Parquet format.
2024-01-01 18:45:13,703 - root - INFO - Converted machine-27-0.csv to Parquet format successfully.
2024-01-01 18:45:13,703 - root - INFO - Starting to convert machine-28-0.csv CSV file to Parquet format.
2024-01-01 18:45:13,856 - root - INFO - Converted machine-28-0.csv to Parquet format successfully.
2024-01-01 18:45:13,856 - root - INFO - Starting to convert machine-29-0.csv CSV file to Parquet format.
2024-01-01 18:45:14,010 - root - INFO - Converted machine-29-0.csv to Parquet format successfully.
2024-01-01 18:45:14,010 - root - INFO - Starting to convert machine-3-0.csv CSV file to Parquet format.
2024-01-01 18:45:14,161 - root - INFO - Converted machine-3-0.csv to Parquet format successfully.
2024-01-01 18:45:14,161 - root - INFO - Starting to convert machine-30-0.csv CSV file to Parquet format.
2024-01-01 18:45:14,318 - root - INFO - Converted machine-30-0.csv to Parquet format successfully.
2024-01-01 18:45:14,318 - root - INFO - Starting to convert machine-31-0.csv CSV file to Parquet format.
2024-01-01 18:45:14,472 - root - INFO - Converted machine-31-0.csv to Parquet format successfully.
2024-01-01 18:45:14,473 - root - INFO - Starting to convert machine-32-0.csv CSV file to Parquet format.
2024-01-01 18:45:14,630 - root - INFO - Converted machine-32-0.csv to Parquet format successfully.
2024-01-01 18:45:14,631 - root - INFO - Starting to convert machine-33-0.csv CSV file to Parquet format.
2024-01-01 18:45:14,785 - root - INFO - Converted machine-33-0.csv to Parquet format successfully.
2024-01-01 18:45:14,785 - root - INFO - Starting to convert machine-34-0.csv CSV file to Parquet format.
2024-01-01 18:45:14,940 - root - INFO - Converted machine-34-0.csv to Parquet format successfully.
2024-01-01 18:45:14,940 - root - INFO - Starting to convert machine-35-0.csv CSV file to Parquet format.
2024-01-01 18:45:15,094 - root - INFO - Converted machine-35-0.csv to Parquet format successfully.
2024-01-01 18:45:15,094 - root - INFO - Starting to convert machine-36-0.csv CSV file to Parquet format.
2024-01-01 18:45:15,247 - root - INFO - Converted machine-36-0.csv to Parquet format successfully.
2024-01-01 18:45:15,247 - root - INFO - Starting to convert machine-37-0.csv CSV file to Parquet format.
2024-01-01 18:45:15,405 - root - INFO - Converted machine-37-0.csv to Parquet format successfully.
2024-01-01 18:45:15,406 - root - INFO - Starting to convert machine-38-0.csv CSV file to Parquet format.
2024-01-01 18:45:15,567 - root - INFO - Converted machine-38-0.csv to Parquet format successfully.
2024-01-01 18:45:15,567 - root - INFO - Starting to convert machine-39-0.csv CSV file to Parquet format.
2024-01-01 18:45:15,724 - root - INFO - Converted machine-39-0.csv to Parquet format successfully.
2024-01-01 18:45:15,724 - root - INFO - Starting to convert machine-4-0.csv CSV file to Parquet format.
2024-01-01 18:45:15,871 - root - INFO - Converted machine-4-0.csv to Parquet format successfully.
2024-01-01 18:45:15,871 - root - INFO - Starting to convert machine-40-0.csv CSV file to Parquet format.
2024-01-01 18:45:16,024 - root - INFO - Converted machine-40-0.csv to Parquet format successfully.
2024-01-01 18:45:16,024 - root - INFO - Starting to convert machine-41-0.csv CSV file to Parquet format.
2024-01-01 18:45:16,175 - root - INFO - Converted machine-41-0.csv to Parquet format successfully.
2024-01-01 18:45:16,175 - root - INFO - Starting to convert machine-42-0.csv CSV file to Parquet format.
2024-01-01 18:45:16,356 - root - INFO - Converted machine-42-0.csv to Parquet format successfully.
2024-01-01 18:45:16,356 - root - INFO - Starting to convert machine-43-0.csv CSV file to Parquet format.
2024-01-01 18:45:16,508 - root - INFO - Converted machine-43-0.csv to Parquet format successfully.
2024-01-01 18:45:16,508 - root - INFO - Starting to convert machine-44-0.csv CSV file to Parquet format.
2024-01-01 18:45:16,657 - root - INFO - Converted machine-44-0.csv to Parquet format successfully.
2024-01-01 18:45:16,658 - root - INFO - Starting to convert machine-45-0.csv CSV file to Parquet format.
2024-01-01 18:45:16,819 - root - INFO - Converted machine-45-0.csv to Parquet format successfully.
2024-01-01 18:45:16,820 - root - INFO - Starting to convert machine-46-0.csv CSV file to Parquet format.
2024-01-01 18:45:16,977 - root - INFO - Converted machine-46-0.csv to Parquet format successfully.
2024-01-01 18:45:16,978 - root - INFO - Starting to convert machine-47-0.csv CSV file to Parquet format.
2024-01-01 18:45:17,136 - root - INFO - Converted machine-47-0.csv to Parquet format successfully.
2024-01-01 18:45:17,136 - root - INFO - Starting to convert machine-48-0.csv CSV file to Parquet format.
2024-01-01 18:45:17,287 - root - INFO - Converted machine-48-0.csv to Parquet format successfully.
2024-01-01 18:45:17,288 - root - INFO - Starting to convert machine-49-0.csv CSV file to Parquet format.
2024-01-01 18:45:17,448 - root - INFO - Converted machine-49-0.csv to Parquet format successfully.
2024-01-01 18:45:17,448 - root - INFO - Starting to convert machine-5-0.csv CSV file to Parquet format.
2024-01-01 18:45:17,602 - root - INFO - Converted machine-5-0.csv to Parquet format successfully.
2024-01-01 18:45:17,602 - root - INFO - Starting to convert machine-50-0.csv CSV file to Parquet format.
2024-01-01 18:45:17,762 - root - INFO - Converted machine-50-0.csv to Parquet format successfully.
2024-01-01 18:45:17,762 - root - INFO - Starting to convert machine-6-0.csv CSV file to Parquet format.
2024-01-01 18:45:17,919 - root - INFO - Converted machine-6-0.csv to Parquet format successfully.
2024-01-01 18:45:17,919 - root - INFO - Starting to convert machine-7-0.csv CSV file to Parquet format.
2024-01-01 18:45:18,072 - root - INFO - Converted machine-7-0.csv to Parquet format successfully.
2024-01-01 18:45:18,072 - root - INFO - Starting to convert machine-8-0.csv CSV file to Parquet format.
2024-01-01 18:45:18,226 - root - INFO - Converted machine-8-0.csv to Parquet format successfully.
2024-01-01 18:45:18,226 - root - INFO - Starting to convert machine-9-0.csv CSV file to Parquet format.
2024-01-01 18:45:18,380 - root - INFO - Converted machine-9-0.csv to Parquet format successfully.
2024-01-01 18:45:23,159 - root - INFO - Concatenated parquet files into ../../data/machines_parquet/machine_all_parquet
2024-01-01 18:45:25,142 - root - INFO - Starting to read the Material Excel file.
2024-01-01 18:45:26,424 - root - INFO - Successfully read the Material Excel file into a DataFrame.
2024-01-01 18:45:27,135 - root - INFO - Starting to read the Material Excel file.
2024-01-01 18:45:30,543 - root - INFO - Successfully read the Material Excel file into a DataFrame.
2024-01-01 18:45:33,109 - root - WARNING - The Sales Excel file is empty. Skipping file processing.
2024-01-01 18:45:34,580 - root - INFO - Starting to read the Supply Chain Parquet file from ../../data/machines_parquet/machine_all_parquet.
2024-01-01 18:54:39,220 - root - INFO - Successfully read the Supply Chain Parquet file from ../../data/machines_parquet/machine_all_parquet into a DataFrame.
2023-12-29 18:54:40,531 - root - INFO - Starting to transform DataFrame for dim_material_prices table.
2023-12-29 18:54:41,534 - root - INFO - Successfully transformed DataFrame for dim_material_price table.
2023-12-29 18:54:41,731 - root - INFO - Starting to transform DataFrame for dim_part_information table.
2023-12-29 18:56:43,111 - root - INFO - Successfully transformed DataFrame for dim_part_information table.
2023-12-29 18:56:44,034 - root - INFO - Starting to transform DataFrame for dim_machine table.
2023-12-29 18:56:46,171 - root - INFO - Successfully transformed DataFrame for dim_machine table.
2023-12-29 18:56:47,194 - root - INFO - Starting to transform DataFrame for dim_machine table.
2023-12-29 18:56:50,265 - root - INFO - Successfully transformed DataFrame for dim_machine table.
2023-12-29 18:56:50,697 - root - INFO - Starting to transform DataFrame for fact_sales table.
2023-12-29 18:58:50,209 - root - INFO - Successfully transformed DataFrame for fact_sales table.
2023-12-29 19:00:14,123 - root - INFO - Starting to transform DataFrame for dim_time table.
2023-12-29 19:00:56,898 - root - INFO - Successfully transformed DataFrame for dim_time table.
2023-12-29 19:00:57,097 - root - INFO - Starting to transform DataFrame for fact_supply_chain table.
2023-12-29 19:04:09,655 - root - INFO - Successfully transformed DataFrame for fact_supply_chain table.
2023-12-29 19:04:15,235 - root - INFO - Data inserted into the ODS dim_material table successfully.
2023-12-29 19:04:29,432 - root - INFO - Data inserted into the ODS dim_part_information table successfully.
2023-12-29 19:04:32,507 - root - INFO - Data inserted into the ODS dim_machine table successfully.
2023-12-29 19:04:52,789 - root - INFO - Data inserted into the ODS dim_contract table successfully.
2023-12-29 19:05:01,262 - root - INFO - Data inserted into the ODS dim_time table successfully.
2023-12-29 19:05:10,673 - root - INFO - Data inserted into the ODS fact_sales table successfully.
2023-12-29 19:14:31,322 - root - INFO - Data inserted into the ODS fact_supply_chain table successfully.
```
### Data Warehousing - Star Schema Data Modeling
In this section, we've followed the standards behind the Kimball Dimensional Modeling Database. 

Kimball data modeling's approach optimizes data for efficient querying and analysis, focusing on ease of understanding and accessibility for business users whereas OLTP databases aren't ideal for analytics due to their normalized structure, which prioritizes transaction processing and data integrity but results in complex queries and slower performance for analytical purposes.

<img src="https://i.imgur.com/qzGddmW.jpg" alt="dwh-3-1" style="max-width:100%; max-height:100%;" border="0">

### Data Storage Infrastructure
#### Data Warehouse Restore and Replication Strategy
Backup and restore scripts for the DWH database are declared in the ``infrastructure`` folder.

Generate a backup storage by running this command:
```
sqlcmd -S <your-local-machine> -E -i "./scripts/infrastructure/dwh/trigger_backup_dwh_production.sql"
```
Then at anytime you might run this command in order to restore the database by an existant backup storage (replace the name of the backup file ``.bak`` by the backup file of your choice):

```
sqlcmd -S <your-local-machine> -E -i "./scripts/infrastructure/dwh/restore_dwh_production.sql"
```

Replication is supported by SQL Server's Replication Wizard to configure replication. You'll have to set up Publications (database objects to replicate), Subscriptions (destination servers), Articles (tables, views, etc.), and Replication Agents (processes responsible for data copying).

#### File version history
All the files are persisted in an azure container using the Azure Blob Storage service. The blobs are persisted in a cool storage tier and the cluster is deployed on a LRS (Local Redundant Storage) strategy.

### Kafka Consumer System
Before running the main job runner, please make sure that the Kafka broker is already up and that communication is established between the kafka producer and the kafka consumer. Check out the [back-end repository](https://github.com/4PROJ-5PROJ-Namkin/microservice-backend/tree/main) to launch the Kafka Broker.

If no broker is still unavailable, it only mean that the IP address cannot resolve the hostname. To solve this issue, follow these steps:
#### In Windows:
1. Type the following command:
```
notepad C:\Windows\System32\drivers\etc\hosts
```
2. Add a new line and save the file:
```
127.0.0.1 kafka
```

#### In Linux:
1. Type the following command:
```
sudo nano /etc/hosts
```
2. Add a new line and save the file:
```
127.0.0.1 kafka
```

Finally, the Kafka Consumer will consume all the message from countless topics. Upsert or delete operation will be heavilly performed on the ODS.

For each topic message received, you'll have to run this script in order to bring up to date the data warehouse by running this script in a native SQL Server engine rather than using a JDBC connector:
```
sqlcmd -S <your-local-machine> -E -i "./scripts/infrastructure/dwh/dwh_truncate_and_bulk_massive_inserts_<table-name>_table.sql
```
Replace the table name by the specific fact or dimension table corresponding to the topic message name.







