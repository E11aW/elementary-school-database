# extract_schema.py
# Sam Baranov
import os


def extract_schema(input_file='NorthEastElementary.txt', output_file='schema.sql'):
    '''
    Used to extract the schema from the initial SQL file that we had to test
our database against. Schema is needed to setup the database using the db_setup scripts.
'''
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        # Find the schema part (between first BEGIN; and COMMIT; before the data loading part)
        schema_start = content.find('BEGIN;')
        schema_end = content.find('COMMIT;', schema_start) + len('COMMIT;')
        schema_sql = content[schema_start:schema_end]
        
        with open(output_file, 'w') as f:
            f.write(schema_sql)
        
        print(f"Schema SQL extracted and saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error extracting schema: {e}")
        return False

if __name__ == "__main__":
    # Check if NorthEastElementary.txt exists in the current directory, needed to run this script manually
    if not os.path.exists('NorthEastElementary.txt'):
        print("Error: NorthEastElementary.txt is not in the current directory. Please make sure it exists in the current directory.")
    else:
        extract_schema()
