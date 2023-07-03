import os
import csv
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

# Drop the table if it exists
try:
    cursor.execute("DROP TABLE IF EXISTS instapro.service_dim CASCADE")
    cursor.execute("DROP TABLE IF EXISTS instapro.event_fact CASCADE")
    cursor.execute("DROP TABLE IF EXISTS instapro.event_dim CASCADE")
    cursor.execute("DROP TABLE IF EXISTS instapro.professional_dim CASCADE")
    logging.info('Dropped tables if they exist')
except psycopg2.Error as e:
    logging.error(f'Failed to drop tables: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise

# Create the table in the database if it doesn't exist
try:
    # Create dimension table for services
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instapro.service_dim (
            id SERIAL PRIMARY KEY,
            service_id INT UNIQUE,
            service_name_nl VARCHAR,
            service_name_en VARCHAR,
            lead_fee DECIMAL(10, 2)
        )
    ''')

    # Create dimension table for events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instapro.event_dim (
            event_type_id SERIAL PRIMARY KEY,
            event_type VARCHAR
        )
    ''')

    # Create dimension table for professionals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instapro.professional_dim (
            professional_id SERIAL PRIMARY KEY,
            professional_id_anonymized INT
        )
    ''')

    # Create fact table for events
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS instapro.event_fact (
            event_fact_id SERIAL PRIMARY KEY,
            event_id INT,
            event_type VARCHAR,
            professional_id_anonymized INT,
            created_at DATE,
            service_id INT REFERENCES instapro.service_dim (service_id)
        )
    ''')

    # Add indexes to the dimension tables
    cursor.execute('CREATE INDEX idx_event_id ON instapro.event_dim (event_type_id)')
    cursor.execute('CREATE INDEX idx_professional_id_anonymized ON instapro.professional_dim (professional_id)')
    cursor.execute('CREATE INDEX idx_service_id ON instapro.service_dim (service_id)')

    logging.info('Created table if it does not exist')

    cursor.execute("SELECT * FROM instapro.event_log")

    # Fetch all rows from the result set
    rows = cursor.fetchall()

    for row in rows:
        (
            event_id, event_type, professional_id_anonymized,
            created_at, service_id, service_name_nl, service_name_en, lead_fee
        ) = row

        # Replace missing values with default values
        service_name_nl = service_name_nl or ''
        service_name_en = service_name_en or ''
        lead_fee = lead_fee or 0
        
        # Insert into service_dim table (if service_id is not null)
        if service_id:
            cursor.execute(
                '''
                INSERT INTO instapro.service_dim (service_id, service_name_nl, service_name_en, lead_fee)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (service_id) DO NOTHING
                ''',
                (service_id, service_name_nl, service_name_en, lead_fee)
            )
        
        # Insert into event_dim table (if not already exists)
        cursor.execute(
            '''
            INSERT INTO instapro.event_dim (event_type)
            VALUES (%s)
            ''',
            (event_type,)
        )

        # Insert into professional_dim table (if not already exists)
        cursor.execute(
            '''
            INSERT INTO instapro.professional_dim (professional_id_anonymized)
            VALUES (%s)
            ''',
            (professional_id_anonymized,)
        )

        # Insert into event_fact table
        cursor.execute(
            '''
            INSERT INTO instapro.event_fact (event_id, event_type, professional_id_anonymized, created_at, service_id)
            VALUES (%s, %s, %s, %s, %s)
            ''',
            (event_id, event_type, professional_id_anonymized, created_at, service_id,)
        )


    conn.commit()
    logging.info('Data insertion completed successfully.')
except psycopg2.Error as e:
    logging.error(f'Failed to create table: {e}')
    conn.rollback()
    cursor.close()
    conn.close()
    raise
finally:
    cursor.close()
    conn.close()

# Define unit tests for table creation and data insertion
class TestDataInsertion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Connect to the PostgreSQL database
        cls.conn = connect_with_retry()
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.conn.close()

    def test_service_dim_table_created(self):
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'service_dim' AND table_schema = 'instapro')")
        result = self.cursor.fetchone()[0]
        self.assertTrue(result)

    def test_event_dim_table_created(self):
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'event_dim' AND table_schema = 'instapro')")
        result = self.cursor.fetchone()[0]
        self.assertTrue(result)

    def test_professional_dim_table_created(self):
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'professional_dim' AND table_schema = 'instapro')")
        result = self.cursor.fetchone()[0]
        self.assertTrue(result)

    def test_event_fact_table_created(self):
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'event_fact' AND table_schema = 'instapro')")
        result = self.cursor.fetchone()[0]
        self.assertTrue(result)

    def test_service_dim_data_inserted(self):
        self.cursor.execute("SELECT COUNT(*) FROM instapro.service_dim")
        result = self.cursor.fetchone()[0]
        self.assertNotEqual(result, 0)

    def test_event_dim_data_inserted(self):
        self.cursor.execute("SELECT COUNT(*) FROM instapro.event_dim")
        result = self.cursor.fetchone()[0]
        self.assertNotEqual(result, 0)

    def test_professional_dim_data_inserted(self):
        self.cursor.execute("SELECT COUNT(*) FROM instapro.professional_dim")
        result = self.cursor.fetchone()[0]
        self.assertNotEqual(result, 0)

    def test_event_fact_data_inserted(self):
        self.cursor.execute("SELECT COUNT(*) FROM instapro.event_fact")
        result = self.cursor.fetchone()[0]
        self.assertNotEqual(result, 0)

if __name__ == '__main__':
    unittest.main()
