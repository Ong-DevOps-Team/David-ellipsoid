# This module sets up the SQL Server on Azure database connection.
# It also encapsulates the functions for accessing the SQL Server tables.
# All of our SQL statments and DBMS specifics should be encapsulated in this module.
# It also encapsulates the cryptography for encoding/decoding passwords.
#
# Here are the odbc error codes to account for: https://learn.microsoft.com/en-us/sql/odbc/reference/appendixes/appendix-a-odbc-error-codes?view=sql-server-ver16
#
# FIXME: Define and document the well-known-names for the user and the db connection in st.session_state variables that will be used throughout the app.

import streamlit as st
import pyodbc as odbc;
from cryptography.fernet import Fernet
#import base64

class LoginManager:
    def __init__(self) -> None:
        if 'db_connection' not in st.session_state:
            st.session_state['db_connection'] = []  #initialize to prevent re-entry issue where this function called repeatedly before the connection is formed.

            #obtain the key for encrypting and decrypting passwords
            key = st.secrets['FERNET_KEY']
            byte_key = key.encode()
            #byte_key = base64.urlsafe_b64encode(key_str.ljust(32)[:32]) #it turns out this more complete specification is not needed, as the simple key.encode() works.
            st.session_state['crypt_obj'] = Fernet(byte_key)

            #the server, database, username, and password all come from the Azure portal.
            #FIXME: I should load server and database  from the secrets file, like I do for the DB_USERNAME and DB_PASSWORD.
            admin_username = st.secrets["DB_USERNAME"]
            admin_password = '{' + st.secrets["DB_PASSWORD"] + '}'
            server = 'geog495db.database.windows.net'
            database = 'EllipsoidLabs'
            driver= '{ODBC Driver 18 for SQL Server}';  #I got this from an example on the internet.
            connection_str = 'DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+admin_username+';PWD='+ admin_password;
            try:
                st.session_state["db_connection"] = odbc.connect(connection_str)
            except Exception as e:
                error_message = str(e).lower()
                if any(keyword in error_message for keyword in ['timeout', 'connection failed', 'login timeout', 'tcp provider']):
                    raise Exception("Database connection timeout: The database is slow currently. Please try again in 60 seconds.")
                else:
                    # For other connection errors, provide a more specific error message
                    error_code = e.args[0] if e.args else "Unknown"
                    raise Exception(f"Database connection failed: Error code {error_code}. Please contact support if this persists.")
 
    def match_username_and_password(self, username, password) -> bool:
        if username is None:
            return False
        if password is None:
            return False
        if 'db_connection' not in st.session_state:
            return False
        logged_in = False
        try:
            with st.session_state.db_connection.cursor() as cursor:
                #be careful about SQL Injection here.  Took recommendation from https://youtu.be/2drXyuLDMQs on string formatting.
                #FIXME: I am not sure this will resolve the issue, so look into this further and experiement.
                sql_statement = "SELECT * FROM dbo.USERS WHERE USERNAME = '%s'" % username
                cursor.execute(sql_statement)
                row = cursor.fetchone()
                while row:
                    #the password is the third column (i.e., row[2]), then use str(decrypted_password, 'utf8') to get rid of the b prefix and the quotes
                    crypt_obj = st.session_state.crypt_obj
                    decrypted_password = crypt_obj.decrypt(row[2])
                    if str(decrypted_password, "utf8") == password:
                        logged_in = True
                        break   #in case there are duplicate usernames, which should never be the case
                    else:
                        logged_in = False #not necessary, as this is the default value, but better to be explicit
                        break;
        except Exception as e:
            # Check if this is a database timeout or connection error
            error_message = str(e).lower()
            if any(keyword in error_message for keyword in ['timeout', 'connection failed', 'login timeout', 'tcp provider']):
                raise Exception("Database connection timeout: The database is slow currently. Please try again in 60 seconds.")
            else:
                # Re-raise other exceptions with a more user-friendly message
                raise Exception("Authentication error: Database connection failed")
        
        st.session_state['user_logged_in'] = logged_in
        return logged_in

    def insert_new_user(self, username, password) -> bool:
        if username is None:
            return False
        if password is None:
            return False
        if 'db_connection' not in st.session_state:
            return False
        with st.session_state.db_connection.cursor() as cursor:
            crypt_obj = st.session_state.crypt_obj
            encrypted_password = crypt_obj.encrypt(str.encode(password))
            #it is byte encoded, so use str(encrypted_password, "utf8") to get rid of the b prefix and the quotes around the string
            sql_statement = "INSERT INTO USERS (username, password) VALUES ('{}', '{}')".format(username, str(encrypted_password, "utf8"))
            cursor.execute(sql_statement)
        return True

    def update_username(self, old_username, new_username):
        pass

    def update_password(self, username, new_password):
        pass

    #FIXME: Here I am returning either false or user info, which is inconsistent.  Should probably return a null list instead of false, but check how the code is used.
    def read_all_users(self):
        if 'db_connection' not in st.session_state:
            return False
        user_info = []
        with st.session_state.db_connection.cursor() as cursor:
            sql_statement = 'SELECT  * FROM  USERS'
            rows = cursor.execute(sql_statement)
            for row in rows:
                user_info.append(row)
        return user_info

    #the streamlist st.button on_click got a strange error when the function only had one parameter; so, I added dummy
    def delete_user(self, username, dummy):
        if username is None:
            return False
        if 'db_connection' not in st.session_state:
            return False
        with st.session_state.db_connection.cursor() as cursor:
            sql_statement = "DELETE FROM USERS WHERE USERNAME = '{}'".format(username)
            cursor.execute(sql_statement)

