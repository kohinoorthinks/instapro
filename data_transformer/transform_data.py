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

# Drop the availability_snapshot table if it exists
cursor.execute("DROP TABLE IF EXISTS instapro.availability_snapshot")

# Create the availability_snapshot table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS instapro.availability_snapshot (
        date DATE PRIMARY KEY,
        active_professionals_count INTEGER
    )
''')
logging.info('Created availability_snapshot table if it does not exist')

# Get the minimum timestamp from the event_fact table
cursor.execute('SELECT MIN(created_at) FROM instapro.event_fact')
min_timestamp = cursor.fetchone()[0]

# Set the end date for the availability snapshot
end_date = '2020-03-10'

# Generate the availability snapshot data
cursor.execute('''
    INSERT INTO instapro.availability_snapshot (date, active_professionals_count)
    SELECT
        gs.date AS date,
        COUNT(DISTINCT CASE WHEN instapro.event_fact.event_type = 'became_able_to_propose' THEN instapro.event_fact.professional_id_anonymized END) AS active_professionals_count
    FROM
        generate_series(%s::date, %s::date, '1 day') AS gs(date)
    LEFT JOIN
        instapro.event_fact ON gs.date >= instapro.event_fact.created_at::date
                       AND gs.date < instapro.event_fact.created_at::date + 1
    GROUP BY
        gs.date
''', (min_timestamp, end_date))
logging.info('Availability snapshot data inserted successfully.')

# Commit the changes
conn.commit()
logging.info('Data insertion completed successfully.')

# Close the cursor and connection
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

    def test_availability_snapshot_table_created(self):
        self.cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'availability_snapshot')")
        result = self.cursor.fetchone()[0]
        self.assertTrue(result, 'availability_snapshot table was not created')

    def test_availability_snapshot_data_inserted(self):
        self.cursor.execute('SELECT COUNT(*) FROM instapro.availability_snapshot')
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 0, 'No data inserted into availability_snapshot table')

if __name__ == '__main__':
    unittest.main()
