#Utilities

manage_users.py - list, create, and delete users in the Azure SQL Server database
setup_database.sql - SQL script to create the users table
generate_encryption_key.py - generates a new fernet key
test_fernet_key.py - test the fernet key

To run manage_users, go to the project root directory and use streamlit to run the app:
streamlit run utils\manage_users.py

NOTE: the mongo_access.py is for a not-yet-created Mongo CRUD tool

To set up this in a new project so that these utils also run, along with the backend and frontend, use:
pip install -r reqdev_requirements.txt

These utils may use the secrets.toml file in the .streamlit folder.

These utils are included in the git repo, but should not be deployed to poduction.
