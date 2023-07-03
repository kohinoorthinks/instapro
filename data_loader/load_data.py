import csv
import os
import psycopg2
import json
import yaml
import logging
import unittest
from psycopg2 import OperationalError
from time import sleep

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration values from values.yaml
try:
    with open('values.yaml', 'r') as f:
        config = yaml.safe_load(f)

    DB_HOST = config['postgresql']['host']
    DB_PORT = config['postgresql']['port']
    DB_NAME = config['postgresql']['database']
    DB_USER = config['postgresql']['username']
    DB_PASSWORD = config['postgresql']['postgresPassword']

except (FileNotFoundError, KeyError) as e:
    logging.error(f'Failed to load configuration from values.yaml: {e}')
    raise

# CSV file path
CSV_FILE = os.path.join('data', 'event_log.csv')

# Maximum number of connection retries
MAX_RETRIES = 5
# Delay between connection retries (in seconds)
RETRY_DELAY = 5

def connect_with_retry():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logging.info('Connected to the PostgreSQL database')
            return conn
        except OperationalError as e:
            logging.warning(f'Failed to connect to the PostgreSQL database: {e}')
            logging.info(f'Retrying connection after {RETRY_DELAY} seconds...')
            retries += 1
            sleep(RETRY_DELAY)

    logging.error(f'Failed to connect to the PostgreSQL database after {MAX_RETRIES} retries')
    raise

# Connect to the PostgreSQL database
conn = connect_with_retry()

# Create a cursor object
cursor = conn.cursor()

# Drop the schema if it exists
try:
    cursor.execute("DROP SCHEMA IF EXISTS instapro CASCADE")
    logging.info('Dropped schema if it exists')
except psycopg2.Error as e:
    logging.error(f'Failed to drop schema: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise

# Create the schema
try:
    cursor.execute("CREATE SCHEMA instapro")
    logging.info('Created schema')
except psycopg2.Error as e:
    logging.error(f'Failed to create schema: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise

# Drop the table if it exists
try:
    cursor.execute("DROP TABLE IF EXISTS instapro.event_log")
    logging.info('Dropped table if it exists')
except psycopg2.Error as e:
    logging.error(f'Failed to drop table: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise

# Create the table in the database if it doesn't exist
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instapro.event_log (
            event_id VARCHAR,
            event_type VARCHAR,
            professional_id_anonymized VARCHAR,
            created_at VARCHAR,
            service_id VARCHAR,
            service_name_nl VARCHAR,
            service_name_en VARCHAR,
            lead_fee VARCHAR
        )
    """)
    logging.info('Created table if it does not exist')
except psycopg2.Error as e:
    logging.error(f'Failed to create table: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise

try:
    with open(CSV_FILE, 'r') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            event_id = row['event_id']
            event_type = row['event_type']
            professional_id = row['professional_id_anonymized']
            created_at = row['created_at']
            meta_data = row['meta_data']

            # Extract information from meta_data using the pattern: {service_id}_{service_name_nl}_{service_name_en}_{lead_fee}
            parts = meta_data.split('_')
            
            if len(parts) != 4:
                logging.warning(f'Invalid meta_data format for event_id {event_id}. Populating with NULL values.')
                service_id = None
                service_name_nl = None
                service_name_en = None
                lead_fee = None
            else:
                try:
                    service_id = int(parts[0])
                    service_name_nl = parts[1]
                    service_name_en = parts[2]
                    lead_fee = float(parts[3])
                except (ValueError, TypeError):
                    logging.warning(f'Invalid values in meta_data for event_id {event_id}. Populating with NULL values.')
                    service_id = None
                    service_name_nl = None
                    service_name_en = None
                    lead_fee = None
            
            cursor.execute("""
                INSERT INTO instapro.event_log (event_id, event_type, professional_id_anonymized, created_at, service_id, service_name_nl, service_name_en, lead_fee)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (event_id, event_type, professional_id, created_at, service_id, service_name_nl, service_name_en, lead_fee))
    
    logging.info('Loaded data from CSV file')
    
except (FileNotFoundError, csv.Error, psycopg2.Error) as e:
    logging.error(f'Failed to load data from CSV file: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise


# Commit the changes and close the connection
try:
    conn.commit()
    logging.info('Changes committed to the database')
except psycopg2.Error as e:
    logging.error(f'Failed to commit changes: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise

cursor.close()
conn.close()
logging.info('Database connection closed')


class TestDataLoading(unittest.TestCase):
    def setUp(self):
        # Connect to the PostgreSQL database
        try:
            self.conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self.cursor = self.conn.cursor()
        except psycopg2.Error as e:
            logging.error(f'Failed to connect to the PostgreSQL database: {e}')
            raise

    def tearDown(self):
        # Rollback changes and close the connection
        try:
            self.conn.rollback()
            self.cursor.close()
            self.conn.close()
            logging.info('Database connection closed')
        except psycopg2.Error as e:
            logging.error(f'Failed to close the database connection: {e}')
            raise

    def test_table_exists(self):
        # Check if the table exists
        try:
            self.cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'event_log')")
            result = self.cursor.fetchone()[0]
            self.assertTrue(result)
        except psycopg2.Error as e:
            logging.error(f'Failed to execute SQL query: {e}')
            raise

    def test_data_loaded(self):
        # Check if data is loaded in the table
        try:
            self.cursor.execute("SELECT COUNT(*) FROM instapro.event_log")
            result = self.cursor.fetchone()[0]
        
            # Get the row count from the CSV file
            with open(CSV_FILE, 'r') as file:
                reader = csv.reader(file)
                csv_row_count = sum(1 for _ in reader) - 1  # Subtract 1 to exclude the header row
        
            self.assertEqual(result, csv_row_count)
        except psycopg2.Error as e:
            logging.error(f'Failed to execute SQL query: {e}')
            raise


    def test_data_accuracy(self):
        # Check the accuracy of the loaded data
        try:
            self.cursor.execute("SELECT event_id FROM instapro.event_log WHERE event_id = '1'")
            result = self.cursor.fetchone()[0]
            self.assertEqual(result, '1')
        except psycopg2.Error as e:
            logging.error(f'Failed to execute SQL query: {e}')
            raise


if __name__ == '__main__':
    unittest.main()
