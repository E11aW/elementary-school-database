# findGuardianNumber.py
import psycopg2

class findGuardianNumber:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.first_name = None
        self.last_name = None
        self.phone_number = None
        self.guardian_details = None  # Will hold additional information

    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares server‑side prepared statements for finding guardian details.
        Two prepared statements are created:
          - One for searching by first name and last name.
          - One for searching by phone number.
        Both now return additional information about the guardian.
        The persistent connection and prepared statement names are stored as class variables.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            # Establish a persistent connection for prepared statements.
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            
            # Prepare statement for searching by first name and last name.
            stmt_name = """
                PREPARE find_guardian_by_name_plan (text, text) AS
                SELECT Number, FirstName, LastName, PhoneNumber, Email
                FROM Guardian
                WHERE FirstName = $1 AND LastName = $2;
            """
            cursor.execute(stmt_name)
            
            # Prepare statement for searching by phone number.
            stmt_phone = """
                PREPARE find_guardian_by_phone_plan (text) AS
                SELECT Number, FirstName, LastName, PhoneNumber, Email
                FROM Guardian
                WHERE PhoneNumber = $1;
            """
            cursor.execute(stmt_phone)
            
            connection.commit()
            cursor.close()
            
            # Store the persistent connection and prepared statement names as class variables.
            cls.prepared_conn = connection
            cls.prepared_statement_name = "find_guardian_by_name_plan"
            cls.prepared_statement_phone = "find_guardian_by_phone_plan"
            print("Prepared statements for findGuardianNumber.")
        except Exception as e:
            print("Error preparing statement for findGuardianNumber:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return "Finds detailed guardian information based on either (1) First Name & Last Name or (2) Phone Number."

    def getInput(self, first_name=None, last_name=None, phone_number=None):
        """
        Takes either (1) First Name & Last Name OR (2) Phone Number as input.
        If no input is provided, prompts the user.
        """
        if first_name and last_name:
            self.first_name = first_name
            self.last_name = last_name
        elif phone_number:
            self.phone_number = phone_number
        else:
            print("\nSearch Guardian by:")
            print("1. First Name & Last Name")
            print("2. Phone Number")
            choice = input("Enter choice (1 or 2): ").strip()

            if choice == "1":
                self.first_name = input("Enter Guardian's First Name: ").strip()
                self.last_name = input("Enter Guardian's Last Name: ").strip()
            elif choice == "2":
                self.phone_number = input("Enter Guardian's Phone Number: ").strip()
            else:
                print("Invalid choice. Please try again.")
                self.getInput()  # Recurse for valid input

    def retrieveOutput(self):
        """
        Retrieves detailed guardian information using the prepared statements.
        It uses the persistent connection created in prepareStatements().
        """
        try:
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()

            if self.first_name and self.last_name:
                # Execute the prepared statement for name-based search.
                exec_query = f"EXECUTE {self.__class__.prepared_statement_name} (%s, %s);"
                cursor.execute(exec_query, (self.first_name, self.last_name))
            elif self.phone_number:
                # Execute the prepared statement for phone-based search.
                exec_query = f"EXECUTE {self.__class__.prepared_statement_phone} (%s);"
                cursor.execute(exec_query, (self.phone_number,))
            else:
                print("No valid search parameters provided.")
                return

            result = cursor.fetchone()
            if result:
                self.guardian_details = {
                    "number": result[0],
                    "first_name": result[1],
                    "last_name": result[2],
                    "phone_number": result[3],
                    "email": result[4]
                }
            else:
                self.guardian_details = None

            cursor.close()
            # Note: The persistent connection is not closed here.
        except Exception as e:
            print(f"Error retrieving Guardian details: {e}")

    def displayOutput(self):
        """
        Displays the retrieved detailed guardian information.
        """
        if self.guardian_details:
            print("Guardian Details:")
            print(f"  Guardian Number: {self.guardian_details['number']}")
            print(f"  Name: {self.guardian_details['first_name']} {self.guardian_details['last_name']}")
            print(f"  Phone Number: {self.guardian_details['phone_number']}")
            print(f"  Email: {self.guardian_details['email']}")
        else:
            print("No Guardian found with the given details.")
