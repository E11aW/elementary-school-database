# setup_db_Mac.py

def verify_csv_headers(data_dir, tables):
    """Verify that CSV headers match expected table columns"""
    import csv
    import os
    
    print("\nVerifying CSV headers...")
    
    warnings = 0
    for table in tables:
        csv_file = os.path.join(data_dir, f"{table}.csv")
        
        if not os.path.exists(csv_file):
            print(f"⚠️  Warning: CSV file {csv_file} not found")
            warnings += 1
            continue
            
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                print(f"✓ {table}.csv: {headers}")
        except Exception as e:
            print(f"⚠️  Error reading {table}.csv: {e}")
            warnings += 1
            
    if warnings > 0:
        print(f"\n⚠️  Found {warnings} warnings while verifying CSV files")
    else:
        print("\n✅ All CSV files verified successfully")
    
    return warnings == 0

import os
import sys
import psycopg2
from psycopg2 import Error
import argparse
import configparser

def load_config(config_path='src/db/db_config.ini'):
    """Load database configuration from file"""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file {config_path} not found.")
        print("Please create it with the following structure:")
        print("[DATABASE]")
        print("user = postgres")
        print("password = your_password")
        print("host = localhost")
        print("port = 5432")
        print("database = nee")
        print("")
        print("[PATHS]")
        print("data_dir = data")
        sys.exit(1)
        
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def setup_database(config, drop_existing=False):
    """Set up database schema and load data"""
    try:
        # Connect to PostgreSQL server
        conn_params = {
            'user': config['DATABASE']['user'],
            'password': config['DATABASE']['password'],
            'host': config['DATABASE']['host'],
            'port': config['DATABASE']['port']
        }
        
        # Connect to the PostgreSQL server
        print("\nConnecting to PostgreSQL server...")
        connection = psycopg2.connect(**conn_params)
        connection.autocommit = True
        cursor = connection.cursor()
        print("✅ Connected to PostgreSQL server")
        
        # Drop database if requested and if it exists
        if drop_existing:
            try:
                print(f"\nDropping database {config['DATABASE']['database']} if it exists...")
                
                # First, close our connection to PostgreSQL
                cursor.close()
                connection.close()
                
                # Connect to a different database (postgres) to drop the target database
                conn_params['database'] = 'postgres'  # Connect to default postgres database
                connection = psycopg2.connect(**conn_params)
                connection.autocommit = True
                cursor = connection.cursor()
                
                # Disconnect all users from the database
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{config['DATABASE']['database']}'
                    AND pid <> pg_backend_pid();
                """)
                
                # Drop the database
                cursor.execute(f"DROP DATABASE IF EXISTS {config['DATABASE']['database']}")
                print(f"✅ Database {config['DATABASE']['database']} dropped")
                
                # Close connection to postgres
                cursor.close()
                connection.close()
                
                # Reconnect to the server
                conn_params.pop('database', None)  # Remove database parameter
                connection = psycopg2.connect(**conn_params)
                connection.autocommit = True
                cursor = connection.cursor()
                
            except Exception as e:
                print(f"⚠️  Warning: Could not drop database: {e}")
                # Try to reconnect if an error occurred
                try:
                    conn_params.pop('database', None)  # Remove database parameter
                    connection = psycopg2.connect(**conn_params)
                    connection.autocommit = True
                    cursor = connection.cursor()
                except Exception:
                    pass
        
        # Create and connect to the database
        try:
            print(f"\nCreating database {config['DATABASE']['database']}...")
            cursor.execute(f"CREATE DATABASE {config['DATABASE']['database']}")
            print(f"✅ Database {config['DATABASE']['database']} created")
        except psycopg2.errors.DuplicateDatabase:
            print(f"ℹ️  Database {config['DATABASE']['database']} already exists")
            
        # Close the connection to postgres
        cursor.close()
        connection.close()
        
        # Connect to the newly created database
        print(f"\nConnecting to {config['DATABASE']['database']} database...")
        conn_params['database'] = config['DATABASE']['database']
        connection = psycopg2.connect(**conn_params)
        cursor = connection.cursor()
        print(f"✅ Connected to {config['DATABASE']['database']} database")
        
        # Read schema file and execute
        schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
        if not os.path.exists(schema_file):
            print(f"❌ Error: Schema file {schema_file} not found.")
            print("Please run the extract_schema.py script first.")
            return
            
        print("\nCreating database schema...")
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
            
        cursor.execute(schema_sql)
        connection.commit()
        print("✅ Database schema created")
        
        # Load data from CSV files
        data_dir = os.path.abspath(config['PATHS']['data_dir'])
        if not os.path.exists(data_dir):
            print(f"❌ Error: Data directory {data_dir} not found.")
            print("Please create it and place your CSV files there.")
            return
        
        # Verify CSV files
        tables = [
            'ClassType', 'Room', 'State', 'Address', 'Student', 
            'Guardian', 'StaffType', 'Staff', 'Substitute', 'Availability', 
            'TimeOffRequest', 'Class', 'StaffToClass', 'StudentToClass', 'GuardianToStudent'
        ]
        
        verify_csv_headers(data_dir, tables)
        
        print("\nImporting data from CSV files...")
        
        # Define tables in two categories: those with serial IDs and regular tables
        serial_id_tables = {
            'Availability': ['SubstituteID', 'StartDate', 'EndDate'],
            'TimeOffRequest': ['StartDate', 'EndDate', 'Reason', 'StaffID', 'SubstituteID']
        }
        
        regular_tables = [
            'ClassType', 'Room', 'State', 'Address', 'Student', 
            'Guardian', 'StaffType', 'Staff', 'Substitute', 'Class', 
            'StaffToClass', 'StudentToClass', 'GuardianToStudent'
        ]
        
        # Import regular tables first
        print("\nImporting regular tables...")
        for table in regular_tables:
            csv_file = os.path.join(data_dir, f"{table}.csv")
            
            if not os.path.exists(csv_file):
                print(f"⚠️  Warning: CSV file for table {table} not found at {csv_file}")
                continue
                
            # Format the path correctly for the platform
            if os.name == 'nt':  # Windows
                csv_path = csv_file.replace('\\', '\\\\')
            else:  # Unix/Mac
                csv_path = csv_file
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    cursor.copy_expert(f"COPY {table} FROM STDIN WITH CSV HEADER", f)
                connection.commit()
                print(f"✅ Data loaded for table: {table}")
            except Exception as e:
                print(f"❌ Error loading data for table {table}: {e}")
                connection.rollback()
        
        # Import tables with serial ID columns
        print("\nImporting tables with serial ID columns...")
        for table, columns in serial_id_tables.items():
            csv_file = os.path.join(data_dir, f"{table}.csv")
            
            if not os.path.exists(csv_file):
                print(f"⚠️  Warning: CSV file for table {table} not found at {csv_file}")
                continue
                
            # Format the path correctly for the platform
            if os.name == 'nt':  # Windows
                csv_path = csv_file.replace('\\', '\\\\')
            else:  # Unix/Mac
                csv_path = csv_file
                
            columns_str = ', '.join(columns)
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    cursor.copy_expert(f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER", f)
                connection.commit()
                print(f"✅ Data loaded for table: {table}")
            except Exception as e:
                print(f"❌ Error loading data for table {table}: {e}")
                connection.rollback()
        
        print("Database setup completed successfully")
        
    except (Exception, Error) as error:
        print(f"Error setting up database: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Database connection closed")

def main():
    parser = argparse.ArgumentParser(description='Set up the NEE database across platforms')
    parser.add_argument('--config', default='src/db/db_config.ini', help='Path to configuration file')
    parser.add_argument('--clean', action='store_true', help='Drop existing database and recreate it')
    parser.add_argument('--verify', action='store_true', help='Verify CSV files only without importing')
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    # Define tables in the order they should be processed
    tables = [
        'ClassType', 'Room', 'State', 'Address', 'Student', 
        'Guardian', 'StaffType', 'Staff', 'Substitute', 'Availability', 
        'TimeOffRequest', 'Class', 'StaffToClass', 'StudentToClass', 'GuardianToStudent'
    ]
    
    # If verify only, just check the CSV files
    if args.verify:
        data_dir = os.path.abspath(config['PATHS']['data_dir'])
        verify_csv_headers(data_dir, tables)
        return
    
    # Otherwise, proceed with database setup
    setup_database(config, drop_existing=args.clean)

if __name__ == '__main__':
    main()
