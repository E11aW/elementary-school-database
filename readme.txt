0. Configure your local environment, probably best in the root project directory since it'll differ (I added it to gitignore)
YOU MIGHT NEED TO CHANGE YOUR EXECUTION POLICY TO DO IT OUT OF VSCODE
if so, run this in powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

Setting up environment:
    create: python -m venv myenv
        - or any name instead of myenv, just add it to gitignore

Activate by running activation script, going to have to run every time you open the project,  
you can deactivate by just typing deactivate
    Windows: myenv/Scripts/activate
    Mac: source myenv/bin/activate

Don't forget to pull the requirements if they change, and don't forget to export them into the requirements.txt if needed
    run: pip install -r requirements.txt
    update requirements: pip freeze > requirements.txt

1. Set your postgres credentials in db_config.ini
2. Run schema extraction if you want to with "python extract_schema.py" if there is no schema
3. Setup the database based on generated schema with "python src/db/setup_db.py --clean" for Windows
   or "python src/db/setup_db_Mac.py --clean" for Mac users.
    --clean forces the database drop before the setup