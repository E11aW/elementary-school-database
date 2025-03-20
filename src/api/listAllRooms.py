# listAllRooms.py
# Maxx McArthur
import psycopg2

class listAllRooms:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.rooms = []  # This will store the list of rooms.
        self.filter_capacity = None  # Optional filter for capacity.

    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares a server‑side prepared statement for listing all rooms.
        The statement retrieves the room number, capacity, and phone number.
        It uses a parameter to optionally filter by capacity.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            stmt = """
                PREPARE list_all_rooms_plan(integer) AS
                SELECT Number, Capacity, PhoneNumber
                FROM Room
                WHERE ($1 IS NULL OR Capacity >= $1)
                ORDER BY Number;
            """
            cursor.execute(stmt)
            connection.commit()
            cursor.close()
            
            cls.prepared_conn = connection
            cls.prepared_statement_name = "list_all_rooms_plan"
            print("Prepared statement for listAllRooms.")
        except Exception as e:
            print("Error preparing statement for listAllRooms:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return """Lists all rooms available.

Output:
- Room Number
- Capacity
- Phone Number (if available)

Business purpose:
Allows users to view information about all rooms, with an optional filter by capacity.
"""

    def getInput(self):
        """
        Prompts the user if they want to filter by capacity.
        If yes, asks for the minimum capacity to filter the room list.
        """
        choice = input("Would you like to filter by capacity? (y/n): ").strip().lower()
        if choice == 'y':
            capacity_input = input("Please enter minimum capacity: ").strip()
            try:
                self.filter_capacity = int(capacity_input)
            except ValueError:
                print("Invalid capacity. No filtering will be applied.")
                self.filter_capacity = None
        else:
            self.filter_capacity = None

    def retrieveOutput(self):
        """
        Retrieves room details using the prepared statement.
        If a capacity filter was set, it passes that parameter to the query.
        """
        try:
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            # Use filter_capacity if set, otherwise pass None.
            param = self.filter_capacity if self.filter_capacity is not None else None
            exec_query = f"EXECUTE {self.__class__.prepared_statement_name}(%s);"
            cursor.execute(exec_query, (param,))
            rooms = cursor.fetchall()
            
            self.rooms = []
            for room in rooms:
                self.rooms.append({
                    "number": room[0],
                    "capacity": room[1],
                    "phone_number": room[2]
                })
            
            cursor.close()
        except Exception as e:
            print(f"Error retrieving room details: {e}")

    def displayOutput(self):
        """
        Displays the list of all rooms with their details.
        """
        if not self.rooms:
            print("No rooms found.")
            return
        
        print("\n=== List of All Rooms ===")
        for i, room in enumerate(self.rooms, 1):
            print(f"\n[{i}] Room Number: {room['number']}")
            print(f"    Capacity: {room['capacity']}")
            print(f"    Phone Number: {room['phone_number'] if room['phone_number'] else 'N/A'}")
        print("\n=========================")
