# driver.py
import psycopg2
from psycopg2 import Error
import configparser
import os
from src.api.API_Interaction import API_Interaction

def load_config(config_path='src/db/db_config.ini'):
    # Config should be in the db directory, used it to organize development
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Check if config file exists; if not, warn and exit.
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        print(f"Warning: Configuration file {config_path} not found. Please add a valid config file to the db directory.")
        quit()
    
    return config

def connect_to_database():
    try:
        # Getting credentials
        config = load_config()
        db_config = config['DATABASE']
        
        # For Unix socket connections on Mac, host starts with '/'
        host = db_config.get('host', 'localhost')
        
        # Connect to PostgreSQL
        connection = psycopg2.connect(
            user=db_config['user'],
            password=db_config['password'],
            host=host,
            port=db_config['port'],
            database=db_config['database']
        )
        
        cursor = connection.cursor()
        
        # Display PostgreSQL server information
        print("PostgreSQL server information")
        print(connection.get_dsn_parameters(), "\n")
        
        # Check connection
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        print("You are connected to - ", record, "\n")
        
        return connection, cursor
        
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return None, None



def main():
    # Load configuration and build db_config dictionary
    config = load_config()
    db_config = {
        'user': config['DATABASE']['user'],
        'password': config['DATABASE']['password'],
        'host': config['DATABASE']['host'],
        'port': config['DATABASE']['port'],
        'database': config['DATABASE']['database']
    }
    
    # List of available APIs in the required order first, followed by the remaining ones.
    available_apis = [
        "listAllRooms",
        "listAllClasses",
        "findStaffNumber",
        "fillClass",
        "listStudentsInClass",
        "findStudentNumber",
        "listStudentGuardianInfo",
        "requestTimeOff",
        "suggestSubstitutes",
        "addClass",
        "listStudentClasses",
        "findGuardianNumber"
    ]

    # Create the API Interaction instance, which automatically prepares API statements.
    api_handler = API_Interaction(db_config)

    while True:
        print("\nAvailable APIs:")
        for i, api in enumerate(available_apis, 1):
            print(f"{i}. {api}")

        print("0. Exit")
        choice = input("\nEnter the number of the API you want to use (or 0 to exit): ")

        # Exit condition
        if choice == "0":
            print("Exiting program.")
            break

        # Validate choice and execute the selected API
        try:
            choice = int(choice)
            if 1 <= choice <= len(available_apis):
                selected_api = available_apis[choice - 1]
                print(f"\nExecuting {selected_api}...\n")
                api_handler.execute_api(selected_api)
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Optionally, clean up persistent connections used by prepared statements.
    if hasattr(api_handler, "cleanup"):
        api_handler.cleanup()

# For executing the module directly
if __name__ == "__main__":
    main()
