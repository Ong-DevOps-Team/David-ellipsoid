# Interfacing with Atlas MongoDB 4/4/2024
# Following this tutorial: https://www.youtube.com/watch?v=y7erzBfay-8

import os
import streamlit as st
import bson     #binary JSON
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# Debug control - set to True to enable debug output, False to disable
DEBUG_MODE = False

# Global variables for database connection
database = None
collection = None

def debug_print(message):
    """Print debug messages only if DEBUG_MODE is True"""
    if DEBUG_MODE:
        print(f"DEBUG: {message}")

def initialize_mongo():
    global database, collection
    try:
        debug_print("Creating Mongo Client")
        connection_string = st.secrets["MONGO_CONNECTION_STRING"]
        mongo_client = MongoClient(connection_string)

        # add in your database and collection from Atlas
        debug_print("getting Database from mongo client")
        database = mongo_client.get_database("ellipsoid")
        debug_print("getting Collection from mongo client")
        collection = database.get_collection("saved_chats")
        
        return True
    except Exception as e:
        debug_print(f"Error initializing MongoDB: {e}")
        return False

#CREATE (returns the id of the inserted record)
def create_saved_chat(chatname: str, messages: list):
    global collection
    debug_print(f"Starting create_saved_chat with title: {chatname}")
    
    if collection is None:
        debug_print("Collection is None, initializing MongoDB...")
        if not initialize_mongo():
            debug_print("Failed to initialize MongoDB")
            return None
    
    try:
        # Convert messages to a format suitable for storage
        # Filter out system messages and format for storage
        chat_messages = []
        for msg in messages:
            if msg["role"] != "system":  # Don't save system messages
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        debug_print(f"Prepared {len(chat_messages)} messages for saving")
        
        # Insert new chat into our saved_chats collection in Atlas
        document_to_insert = {
            "chatname": chatname, 
            "messages": chat_messages,
            "timestamp": bson.ObjectId()  # This creates a timestamp
        }
        
        debug_print(f"Inserting document: {document_to_insert}")
        result = collection.insert_one(document_to_insert)
        
        debug_print(f"CREATE: Your chat '{chatname}' ({len(chat_messages)} messages) has been saved.")
        debug_print(f"Insert result: {result.inserted_id}")
        return str(result.inserted_id)
    except Exception as e:
        debug_print(f"Error creating saved chat: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return None

#LIST (i.e., READ ALL, titles only)
def list_saved_chats():
    global collection
    if collection is None:
        if not initialize_mongo():
            return []
    
    try:
        # Read all saved chats, ordered by timestamp (most recent first)
        chat_list = list(collection.find().sort("timestamp", -1))
        saved_chats_list = []
        
        for chat in chat_list:
            chatname = chat.get("chatname", "Untitled")
            chat_id = str(chat.get("_id"))
            saved_chats_list.append({
                "chatname": chatname, 
                "chat_id": chat_id
            })

        return saved_chats_list
    except Exception as e:
        debug_print(f"Error listing saved chats: {e}")
        return []

#READ (i.e., read the named chat)
def read_saved_chat(chat_id: str):
    global collection
    if collection is None:
        if not initialize_mongo():
            return None
    
    try:
        chat_doc = collection.find_one({"_id": bson.ObjectId(chat_id)})
        if chat_doc:
            return chat_doc.get("messages", [])
        return None
    except Exception as e:
        debug_print(f"Error reading saved chat: {e}")
        return None

#UPDATE (new_messages is a list of message dictionaries)
def update_saved_chat(chat_id: str, new_chatname: str, new_messages: list):
    global collection
    if collection is None:
        if not initialize_mongo():
            return False
    
    try:
        # Filter out system messages
        chat_messages = []
        for msg in new_messages:
            if msg["role"] != "system":
                chat_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        collection.update_one(
            {"_id": bson.ObjectId(chat_id)}, 
            {"$set": {"chatname": new_chatname, "messages": chat_messages}}
        )
        
        debug_print(f"UPDATE: Your chat '{new_chatname}' has been updated.")
        return True
    except Exception as e:
        debug_print(f"Error updating saved chat: {e}")
        return False

#DELETE
def delete_saved_chat(chat_id: str):
    global collection
    if collection is None:
        if not initialize_mongo():
            return False
    
    try:
        collection.delete_one({"_id": bson.ObjectId(chat_id)})
        debug_print(f"DELETE: Chat (id = {chat_id}) has been removed.")
        return True
    except Exception as e:
        debug_print(f"Error deleting saved chat: {e}")
        return False

