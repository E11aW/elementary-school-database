# listStudentGuardianInfo.py
# Maxx McArthur
import psycopg2

class listStudentGuardianInfo:
    def __init__(self, db_config):
        """
        Initializes the API instance with database configuration.
        :param db_config: Dictionary containing database connection parameters.
        """
        self.db_config = db_config
        self.student_number = None
        self.guardians = []  # List to hold guardian information

    @classmethod
    def prepareStatements(cls, db_config):
        """
        Prepares a server‑side prepared statement for retrieving guardian information
        for a given student number.
        The statement retrieves the guardian's number, first name, last name, phone number,
        email, and address details (street, city, state, zip) by joining with the address
        and state tables.
        The persistent connection and prepared statement name are stored as class variables.
        
        :param db_config: Dictionary containing database connection parameters.
        """
        try:
            connection = psycopg2.connect(**db_config)
            cursor = connection.cursor()
            stmt = """
                PREPARE list_student_guardian_info_plan (text) AS
                SELECT g.Number, g.FirstName, g.LastName, g.PhoneNumber, g.Email,
                       a.Street, a.City, st.Name as state, a.Zip
                FROM guardian g
                JOIN guardiantostudent sg ON g.ID = sg.GuardianID
                JOIN student s ON sg.StudentID = s.ID
                JOIN address a ON g.AddressID = a.ID
                JOIN state st ON a.StateID = st.ID
                WHERE s.Number = $1;
            """
            cursor.execute(stmt)
            connection.commit()
            cursor.close()
            
            cls.prepared_conn = connection
            cls.prepared_statement_name = "list_student_guardian_info_plan"
            print("Prepared statement for listStudentGuardianInfo.")
        except Exception as e:
            print("Error preparing statement for listStudentGuardianInfo:", e)

    def getDescription(self):
        """
        Returns a description of what this API does.
        """
        return (
            "Lists guardian information for a given student.\n\n"
            "Input:\n"
            "- Student Number\n\n"
            "Output:\n"
            "- For each guardian:\n"
            "  - Guardian Number\n"
            "  - First Name\n"
            "  - Last Name\n"
            "  - Phone Number\n"
            "  - Email\n"
            "  - Address (Street, City, State, Zip)\n\n"
            "Business Purpose:\n"
            "Allows users to retrieve comprehensive guardian details for a specified student."
        )

    def getInput(self, student_number=None):
        """
        Takes the student number as input. If not provided, prompts the user.
        
        :param student_number: The unique student number.
        """
        if student_number:
            self.student_number = student_number
        else:
            self.student_number = input("Enter Student Number: ").strip()

    def retrieveOutput(self):
        """
        Retrieves guardian information for the given student number using the prepared statement.
        It uses the persistent connection created in prepareStatements().
        If the connection is not set, it calls prepareStatements() first.
        """
        try:
            # Fallback: if prepared_conn is not set, prepare the statements.
            if not hasattr(self.__class__, 'prepared_conn'):
                self.__class__.prepareStatements(self.db_config)
                
            connection = self.__class__.prepared_conn
            cursor = connection.cursor()
            exec_query = f"EXECUTE {self.__class__.prepared_statement_name} (%s);"
            cursor.execute(exec_query, (self.student_number,))
            results = cursor.fetchall()
            
            self.guardians = []
            for row in results:
                guardian = {
                    "number": row[0],
                    "first_name": row[1],
                    "last_name": row[2],
                    "phone_number": row[3],
                    "email": row[4],
                    "street": row[5],
                    "city": row[6],
                    "state": row[7],
                    "zip": row[8]
                }
                self.guardians.append(guardian)
            cursor.close()
        except Exception as e:
            print(f"Error retrieving guardian information: {e}")

    def displayOutput(self):
        """
        Displays the retrieved guardian information.
        """
        if not self.guardians:
            print(f"No guardians found for student number {self.student_number}.")
            return
        
        print(f"\n=== Guardian Information for Student {self.student_number} ===")
        for i, guardian in enumerate(self.guardians, 1):
            print(f"\n[{i}] Guardian Number: {guardian['number']}")
            print(f"    Name: {guardian['first_name']} {guardian['last_name']}")
            print(f"    Phone Number: {guardian['phone_number']}")
            print(f"    Email: {guardian['email']}")
            print(f"    Address: {guardian['street']}, {guardian['city']}, {guardian['state']} {guardian['zip']}")
        print("\n========================================================")