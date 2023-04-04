from pymongo.mongo_client import MongoClient
from kanade import cfg
import os


_host = cfg['mongo']['host']
_port = cfg['mongo']['port']
_username = cfg['mongo']['username']
_password = cfg['mongo']['password']


def connect():
    return MongoClient(_host, _port, username=_username, password=_password)


def insert_document(collection, data):
    """
    Function to insert a document into a collection and
    return the document's id.
    """
    return collection.insert_one(data).inserted_id


def find_document(collection, elements, multiple=False):
    """
    Function to retrieve single or multiple documents from a provided
    Collection using a dictionary containing a document's elements.
    """
    if multiple:
        results = collection.find(elements)
        return [r for r in results]
    else:
        return collection.find_one(elements)


def update_document(collection, query_elements, new_values):
    """ Function to update a single document in a collection."""
    collection.update_one(query_elements, {'$set': new_values})


def delete_document(collection, query):
    """ Function to delete a single document from a collection."""
    collection.delete_one(query)


def defaults(collection) -> dict:
    if collection == 'guilds':
        return {
            "logs": {
                "quit": None,
                "kick": None,
                "invites": None,
                "join": None,
                "messages": None,
                "roles": None
            },
            "greetings": {
                "enabled": False,
                "title": "Новый пользователь!",
                "description": "Добро пожаловать на сервер {guild_name}, {user_mention}!",
                "channel": None
            }
        }