from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import udf, from_json, explode, col, to_date, count, monotonically_increasing_id, regexp_replace, lit, date_format, year, sum as sum_, max as max_, expr, month, dayofmonth, quarter
from pyspark.sql.types import ArrayType, StructType, StructField, StringType, DoubleType, DateType, ShortType, LongType, IntegerType, TimestampType
import os
import logging
from py4j.protocol import Py4JJavaError
from dotenv import load_dotenv
from ods_prototype_udf_utils import parse_date, string_to_int_list, convert_timestamp_to_date, generate_random_date, get_current_datetime

def create_spark_session():
    """
    Initialize and return a Spark session with specific configurations.
    """
    try:
        spark = SparkSession.builder \
                .appName("NamkinProductionOdsStarSchema") \
                .config("spark.driver.host", "localhost") \
                .master("local[*]") \
                .config("spark.executor.memory", "4g") \
                .config("spark.driver.memory", "2g") \
                .config("spark.sql.shuffle.partitions", "50") \
                .config("spark.executor.cores", "4") \
                .getOrCreate()
        logging.info("Spark session created successfully.")
        return spark
    except Exception as e:
        logging.error(f'An unexpected error occurred while initializing the Spark Session: {e}')

def convert_csv_to_parquet(input_path, output_path, delimiter=",", header=True, inferSchema=True, partitionBy=None):
    """
    Convert all CSV files in the specified input path to Parquet format with various options and save them to the output path.
    """
    if not os.path.exists(input_path):
        logging.error(f"Input path {input_path} does not exist.")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for file_name in os.listdir(input_path):
        if file_name.endswith(".csv"):
            try:
                logging.info(f"Starting to convert {file_name} CSV file to Parquet format.")
                
                file_path = os.path.join(input_path, file_name)
                df = spark.read.format("csv") \
                        .option("inferSchema", inferSchema) \
                        .option("header", header) \
                        .option("sep", delimiter) \
                        .load(file_path)
                
                output_file_path = os.path.join(output_path, file_name.replace('.csv', ''))
                if partitionBy:
                    df.write.mode('overwrite').partitionBy(partitionBy).parquet(output_file_path)
                else:
                    df.write.mode('overwrite').parquet(output_file_path)
                logging.info(f"Converted {file_name} to Parquet format successfully.")
            except Exception as e:
                logging.error(f"Failed to convert {file_name}: {e}")

def concatenate_parquet_files(input_path, output_file):
    """
    Read all Parquet files in the specified input path and concatenate them into a single DataFrame,
    then save it to the specified output file in Parquet format.
    """
    df = spark.read.format("parquet").load(input_path + "/*")
    df_single_partition = df.repartition(1)

    df_single_partition.write.mode('overwrite').format("parquet").save(output_file)
    logging.info(f"Concatenated parquet files into {output_file}")


def read_parquet_with_spark(file_path, file_name):
    """
    Reads a Parquet file into a Spark DataFrame.
    """
    try:
        logging.info(f"Starting to read the {file_name} Parquet file from {file_path}.")
        df = spark.read.format("parquet").load(file_path)
        logging.info(f"Successfully read the {file_name} Parquet file from {file_path} into a Spark DataFrame.")
        return df
    
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading the {file_name} Parquet file from {file_path}: {e}")
        return None

def read_excel_with_spark(file_path, file_name, sheet_name=None):
    """
    Reads an Excel file into a Spark DataFrame.
    """
    try:
        logging.info(f"Starting to read the {file_name} Excel file.")
        
        read_excel_query = spark.read.format("com.crealytics.spark.excel") \
            .option("header", "true") \
            .option("inferSchema", "true")
        
        if sheet_name:
            read_excel_query = read_excel_query.option("dataAddress", f"{sheet_name}!")
        
        df = read_excel_query.load(file_path)                
        logging.info(f"Successfully read the {file_name} Excel file into a Spark DataFrame.")
        return df

    except Py4JJavaError as e:
        if "java.util.NoSuchElementException: head of empty list" in str(e.java_exception):
            logging.warning(f"The {file_name} Excel file is empty. Skipping file processing.")
            return None
        else:
            logging.error(f"Error occurred while reading the {file_name} Excel file: {e}")
            return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while reading the {file_name} Excel file: {e}")
        return None

def populate_fact_supply_chain_table(fact_supply_chain_df, part_df, material_price_df, machine_df):
    """
    Transforms and populates the fact_supply_chain_table with data from multiple source DataFrames.
    Applies necessary transformations and joins to create a final DataFrame with the required schema.
    """
    try:
        logging.info("Starting to transform DataFrame for fact_supply_chain table.")
        convert_timestamp_to_date_udf = udf(convert_timestamp_to_date, TimestampType())
        
        fact_supply_chain_df = fact_supply_chain_df.withColumn("timeOfProduction", convert_timestamp_to_date_udf(col("timeOfProduction"))) \
                                                .withColumn("timeOfProduction", date_format("timeOfProduction", "yyyy-MM-dd")) \
                                                .withColumn("timeId", expr("concat(year(timeOfProduction), lpad(month(timeOfProduction), 2, '0'), lpad(day(timeOfProduction), 2, '0'))").cast("int"))

        fact_supply_chain_df = fact_supply_chain_df.alias('fact').join(
            part_df.select('partId', 'materialId', 'machineId', 'defaultPrice').alias('part_info'),
            (col('fact.partId') == col('part_info.partId')) &
            (col('fact.machineId') == col('part_info.machineId')),
            'inner'
        )
        
        fact_supply_chain_df = fact_supply_chain_df.join(
            material_price_df.select('id', 'materialId', 'date', 'price').alias('material_price'),
            (col('part_info.materialId') == col('material_price.materialId')) & 
            (year(col('material_price.date')) == year(col('fact.timeOfProduction'))),
            'inner'
        )

        fact_supply_chain_df = fact_supply_chain_df.join(
            machine_df.select('machineId').alias('machine'),
            col('fact.machineId') == col('machine.machineId'),
            'inner'
        )

        output_df = fact_supply_chain_df.select(
            F.col('machine.machineId'),
            F.col('fact.partId'),
            F.col('part_info.materialId'),
            F.col('fact.timeOfProduction'),
            F.col('material_price.price').alias('materialPrice'),
            F.col('fact.timeId'),
            F.col('material_price.date').alias('materialPriceDate'),
            F.col('part_info.defaultPrice').alias('partDefaultPrice'),
            F.col('fact.var5').alias('isDamaged'),
            col('fact.lastUpdate')
        )

        logging.info("Successfully transformed and merged DataFrame for fact_supply_chain table.")
        return output_df

    except Exception as e:
        logging.error(f"An error occurred while transforming the DataFrame for fact_supply_chain table: {e}")
        return None

def populate_dim_material_price_table(material_df, price_col='prices', date_format='MM-dd-yyyy'):
    """
    Transforms and enriches the material DataFrame for the dim_material_price table by exploding 
    the serialized JSON 'prices' column into individual rows with 'price' and 'date' columns.
    
    The 'd' field in the JSON is assumed to be a date string, which is transformed into a date object
    in the format specified by the date_format parameter. The original materialId is preserved.
    """
    try:
        logging.info("Starting to transform DataFrame for dim_material_prices table.")
        dim_schema = ArrayType(StructType([
            StructField("price", DoubleType()),
            StructField("d", StringType())
        ]))
        
        transformed_material_df = material_df.withColumn(price_col, from_json(col(price_col), dim_schema)) \
                                             .withColumn("exploded", explode(col(price_col)))
        
        parse_date_udf = udf(parse_date, DateType())
        
        final_df = transformed_material_df.withColumn("price", col("exploded.price")) \
                                         .withColumn("date", to_date(col("exploded.d"), date_format)) \
                                         .withColumn("lastUpdate", current_datetime_udf()) \
                                         .select(
                                             monotonically_increasing_id().alias("id"),
                                             "name",
                                             "price",
                                             "date",
                                             col("id").alias("materialId"),
                                             "lastUpdate"
                                         )
        
        logging.info("Successfully transformed DataFrame for dim_material_price table.")
        return final_df
    
    except Exception as e:
        logging.error("An error occurred while transforming the DataFrame for dim_material_price table: %s", e)

def populate_dim_part_information_table(part_information_df, material_col='meterials', machine_col='machine'):
    """
    Transforms and enriches the part information DataFrame by exploding the 'machine' and 'meterials' columns.
    """
    try:
        logging.info("Starting to transform DataFrame for dim_part_information table.")

        string_to_int_list_udf = udf(string_to_int_list, ArrayType(IntegerType()))
        part_information_df = part_information_df \
            .withColumn(material_col, regexp_replace(col(material_col), "'", "")) \
            .withColumn(material_col, string_to_int_list_udf(col(material_col))) \
            .withColumn(machine_col, string_to_int_list_udf(col(machine_col)))

        part_information_df = part_information_df \
            .withColumn(material_col, explode(col(material_col))) \
            .withColumn(machine_col, explode(col(machine_col))) \
            .withColumn('id', col('id').cast(ShortType()))
            
        final_df = part_information_df \
            .withColumnRenamed(machine_col, "machineId") \
            .withColumnRenamed(material_col, "materialId") \
            .withColumnRenamed('id', 'partId')
            
        logging.info("Successfully transformed DataFrame for dim_part_information table.")
        return final_df
    
    except Exception as e:
        logging.error(f"An error occurred while transforming the DataFrame: {e}")

def populate_dim_machine_table(part_information_df):
    """
    Transforms and enriches the machine DataFrame by extracting the unique material ids of the part information 
    transformed and leveraged DataFrame in order to ensure referential integrity in both sides.
    """
    try:
        logging.info("Starting to transform DataFrame for dim_machine table.")
        machine_df = part_information_df.select(part_information_df["machineId"], part_information_df["lastUpdate"]) \
                                        .dropDuplicates() \
                                        .orderBy('machineId', ascending=True)
        
        logging.info("Successfully transformed DataFrame for dim_machine table.")
        return machine_df
    except Exception as e:
        logging.error(f"An error occurred while transforming the DataFrame for dim_machine table: {e}")

def populate_fact_sales_table(supply_chain_df, part_df):
    """
    Transforms and prepares a DataFrame for the dim_sales table. This function performs
    several operations including counting quantities of parts, calculating total cash,
    determining the maximum production year, and generating formatted client names.
    """
    try:
        logging.info("Starting to transform DataFrame for dim_sales table.")
        random_date_udf = udf(generate_random_date, DateType())
        convert_timestamp_to_date_udf = udf(convert_timestamp_to_date, TimestampType())

        quantity_df = supply_chain_df.groupBy("order", "partId").agg(count("*").alias("quantity"))

        cost_df = quantity_df.join(part_df, quantity_df.partId == part_df.partId) \
                             .groupBy("order") \
                             .agg(sum_(col("defaultPrice") * col("quantity")).alias("cash"))

        max_year_df = supply_chain_df.withColumn("timeOfProduction", convert_timestamp_to_date_udf(col("timeOfProduction"))) \
                                    .withColumn("timeOfProduction", date_format("timeOfProduction", "yyyy-MM-dd HH:mm:ss.SSS")) \
                                    .groupBy("order", "partId") \
                                    .agg(max_(year(col("timeOfProduction"))).alias("maxYear"))

        sales_df = cost_df.join(max_year_df, "order")
        sales_df = sales_df.withColumn("date", random_date_udf(col("maxYear")))
        sales_df = sales_df.withColumn("clientName", F.expr("concat('CLIENT NO_', order)"))
        sales_df = sales_df.withColumn("lastUpdate",  current_datetime_udf())
        
        final_sales_df = sales_df.select(
            col("order").alias("contractId"),
            "partId",
            "clientName",
            "cash",
            "date",
            "lastUpdate"
        )

        logging.info("Successfully transformed DataFrame for dim_sales table.")
        return final_sales_df

    except Exception as e:
        logging.error(f"An error occurred while transforming the DataFrame for dim_sales table: {e}")
        return None

def populate_dim_time_table():
    """
    Generates a 'dim_time' table with IDs ranging from January 1, 1920 to January 1, 2099.
    The ID is formatted as 'YYYYMMDD'. For example, January 1, 1920 would be 19200101.
    Additional fields for year, month, day, semester, and quarter are derived from the ID.
    """
    try:
        logging.info('Starting to initialize DataFrame for dim_time table.')
        start_date = '1920-01-01'
        end_date = '2099-01-01'
        
        dates_df = spark.range(start=0, end=365*179+44).select(F.expr(f"add_months(date '{start_date}', int(id))").alias('date')).withColumn('date', col('date').cast(DateType()))

        dim_time_df = dates_df.withColumn("year", year(col("date"))) \
                            .withColumn("month", month(col("date"))) \
                            .withColumn("day", dayofmonth(col("date"))) \
                            .withColumn("quarter", quarter(col("date"))) \
                            .withColumn("semester", expr("CASE WHEN quarter IN (1, 2) THEN 1 ELSE 2 END")) \
                            .withColumn("timeId", expr("concat(year(date), lpad(month(date), 2, '0'), lpad(day(date), 2, '0'))").cast("int"))

        dim_time_df = dim_time_df.select("timeId", "date", "year", "month", "day", "semester", "quarter")
        logging.info('Successfully transformer DataFrame for dim_time table.')
        return dim_time_df
    except Exception as e:
        logging.error(f"An error occurred while transforming the DataFrame for dim_time table: {e}")

def export_data_into_ods_table(df, server, database, username, password, table_name):
    """
    Inserts records from a DataFrame into a ODS table persisted in a SQL Server database.
    """
    try:
        jdbc_url = (
            f"jdbc:sqlserver://{server}:1433;"
            f"databaseName={database};"
            f"user={username};"
            f"password={password};"
        )

        df.write \
          .format("jdbc") \
          .option("url", jdbc_url) \
          .option("dbtable", table_name) \
          .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver") \
          .save()
        
        logging.info(f"Data inserted into the ODS {table_name} table successfully.")

    except Exception as e:
        logging.error(f"An error occurred while inserting {table_name} data into SQL Server: {e}")

if __name__ == "__main__":
    log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs', 'ods_populate_tables_star_schema.log'))
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
                    logging.FileHandler(log_file_path),
                    logging.StreamHandler()
                ]
        )
    
    load_dotenv('../../.env')
    server = os.getenv('DB_HOST')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')

    input_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'machines')
    output_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'machines_parquet')
    final_output_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'machines_parquet', 'machines_all_parquet')

    current_datetime_udf = udf(get_current_datetime, StringType())

    spark = create_spark_session()
    convert_csv_to_parquet(input_path, output_path)
    concatenate_parquet_files(output_path, final_output_path)

    material_df = read_excel_with_spark(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'material-data.xlsx') , "Material") \
                    .withColumn("lastUpdate", current_datetime_udf())
    part_information_df = read_excel_with_spark(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'part-reference.xlsx'), "Part Information") \
                            .withColumn("lastUpdate", current_datetime_udf())
    sales_df = read_excel_with_spark(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'sales.xlsx'), "Sales")
    supply_chain_df = read_parquet_with_spark(final_output_path, 'Supply Chain').withColumn("lastUpdate", current_datetime_udf())
    
    material_price_df = populate_dim_material_price_table(material_df)
    part_df = populate_dim_part_information_table(part_information_df)
    machine_df = populate_dim_machine_table(part_df)
    sales_df = populate_fact_sales_table(supply_chain_df, part_df)

    time_df = populate_dim_time_table()
    supply_chain_df = populate_fact_supply_chain_table(supply_chain_df, part_df, material_price_df, machine_df)

    material_df = material_df.withColumn('id', col('id').cast(ShortType())) \
                            .select(col('id').alias('materialId'), 'name', 'lastUpdate')
    part_information_df = part_information_df.withColumn('id', col('id').cast(ShortType())) \
                                            .select(col('id').alias('partId'), 'timeToProduce', 'lastUpdate')
    contract_df = sales_df.select("contractId", "clientName", "lastUpdate").distinct()
    sales_df = sales_df.select('partId', 'contractId', 'cash', 'date', 'lastUpdate')

    try: 
        target_df = [material_df, part_information_df, machine_df, contract_df, time_df, sales_df, supply_chain_df]
        target_tables = ['dim_material', 'dim_part_information', 'dim_machine', 'dim_contract', 'dim_time', 'fact_sales', 'fact_supply_chain']

        for t_df, t_name in zip(target_df, target_tables):
            export_data_into_ods_table(t_df, server, database, username, password, t_name)
    except Exception as e:
        logging.error(f'Failed to serialize the values of the {t_df} DataFrame in the {t_name} table: {e}')
