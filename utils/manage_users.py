# A stand alone program to perform CRUD operations on the ellispoid labs usrs
# Note that we encrypt and decrypt passwords, so we cannot really use SSMS and SQL

import streamlit as st
import login_manager as login_manager_file

#set up database connection
if 'db_connection' not in st.session_state:
    login_manager = login_manager_file.LoginManager()
    st.session_state['login_manager'] = login_manager
else:
    if 'login_manager' in st.session_state:
        login_manager = st.session_state.login_manager

list_section = st.container()
create_section = st.container()
update_username_section = st.container()
update_password_section = st.container()
delete_section = st.container()

with list_section:
    st.write('List Users')
    if st.button('List Users'):
        users = login_manager.read_all_users()
        for user in users:
            st.write(str(user))
            #I am sure there is a nicer way to do this in a table or something

with create_section:
    st.divider()
    st.write('Add User')
    username = st.text_input(label="Username:", value=None, placeholder="Enter your username", max_chars=80)
    password = st.text_input(label="Password:", value=None, placeholder="Enter your password", max_chars=80)
    st.button("Add User", on_click=login_manager.insert_new_user, args=(username, password))


with update_username_section:
    st.divider()
    st.write('Update Username - Delete and Add User')
    #old_username = st.text_input(label="Old Username:", value=None, placeholder="Enter old username", max_chars=80)
    #new_username = st.text_input(label="New username:", value=None, placeholder="Enter new username", max_chars=80)
    #st.button("Update User", on_click=ellipsoid_sql.insert_new_user, args=(old_username, new_username))

with update_password_section:
    st.divider()
    st.write('Update Password - Delete and Add User')
    #username = st.text_input(label="Username To Update Password:", value=None, placeholder="Enter username", max_chars=80)
    #new_password = st.text_input(label="New password:", value=None, placeholder="Enter new password", max_chars=80)
    #st.button("Update Password", on_click=ellipsoid_sql.insert_new_user, args=(username, new_password))

with delete_section:
    st.divider()
    st.write('Delete user')
    username = st.text_input(label="Username to Delete", value=None, placeholder="Enter username", max_chars=80)
    dummy = ''
    #STRANGE BEHAVIOR: I tried making the delete_user function only have one argument, but it got a strange error; giving it two arguments works.
    st.button("Delete A User", on_click=login_manager.delete_user, args=(username, dummy))
