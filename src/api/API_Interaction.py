# API_Interaction.py (part of driver)
# Clayton McArthur 

# APIs
from .listStudentsInClass import listStudentsInClass
from .listStudentGuardianInfo import listStudentGuardianInfo
from .requestTimeOff import requestTimeOff
from .suggestSubstitutes import suggestSubstitutes
from .addClass import addClass
from .fillClass import fillClass
from .listStudentClasses import listStudentClasses
from .listAllClasses import listAllClasses
from .findStudentNumber import findStudentNumber
from .findStaffNumber import findStaffNumber
from .findGuardianNumber import findGuardianNumber
from .listAllRooms import listAllRooms

class API_Interaction:
    def __init__(self, db_config=None):
        # Store database configuration (or connection)
        self.db_config = db_config
        
        # Mapping API names to their respective classes
        self.api_classes = {
            "listStudentsInClass": listStudentsInClass,
            "listStudentGuardianInfo": listStudentGuardianInfo,
            "requestTimeOff": requestTimeOff,
            "suggestSubstitutes": suggestSubstitutes,
            "addClass": addClass,
            "fillClass": fillClass,
            "listStudentClasses": listStudentClasses,
            "listAllClasses": listAllClasses,
            "findStudentNumber": findStudentNumber,
            "findStaffNumber": findStaffNumber,
            "findGuardianNumber": findGuardianNumber,
            "listAllRooms": listAllRooms
        }
        
        # Initialize prepared statements for each API.
        self.prepareStatements()

    def prepareStatements(self):
        """
        Iterate through each API and call its prepareStatements() method.
        This method should be called once during initialization to set up
        all prepared statements for the APIs.
        """
        for name, api_class in self.api_classes.items():
            try:
                # Call the prepareStatements() method on the API class,
                # passing the database connection/configuration.
                api_class.prepareStatements(self.db_config)
                print(f"Prepared statements for API: {name}")
            except AttributeError:
                print(f"API '{name}' does not implement prepareStatements().")
            except Exception as e:
                print(f"Error preparing statements for API '{name}': {e}")

    def execute_api(self, api_name):
        """Executes the API if it exists"""
        if api_name not in self.api_classes:
            print(f"Error: API '{api_name}' not found.")
            return

        # Create an instance of the selected API class with database config
        try:
            api_instance = self.api_classes[api_name](self.db_config)
        except TypeError:
            # Fallback for APIs that don't accept db_config
            api_instance = self.api_classes[api_name]()

        # Execute the API workflow
        print("\n--- API Description ---")
        print(api_instance.getDescription())

        print("\n--- API Input ---")
        api_instance.getInput()

        print("\n--- Retrieving Output ---")
        api_instance.retrieveOutput()

        print("\n--- Displaying Output ---")
        api_instance.displayOutput()