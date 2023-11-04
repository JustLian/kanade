from pymongo.mongo_client import MongoClient
import motor.motor_asyncio
from kanade import cfg
import os


client = None
_host = cfg['mongo']['host']
_port = cfg['mongo']['port']
_username = cfg['mongo']['username']
_password = cfg['mongo']['password']


def connect() -> motor.motor_asyncio.AsyncIOMotorClient:
    global client
    if not client:
        client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://{}:{}@{}:{}/?authMechanism=DEFAULT'.format(_username, _password, _host, _port))
    return client


async def insert_document(collection, data):
    """
    Function to insert a document into a collection and
    return the document's id.
    """
    return await collection.insert_one(data).inserted_id


async def find_document(collection, elements, multiple=False):
    """
    Function to retrieve single or multiple documents from a provided
    Collection using a dictionary containing a document's elements.
    """
    if multiple:
        c = collection.find(elements)
        return await c.to_list()
    else:
        return await collection.find_one(elements)


async def update_document(collection, query_elements, new_values):
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
                "channel": None,
                "color": "#ffffff",
                'glow_color1': '#ffffff',
                'glow_color2': '#ff0000',
                'border_color1': '#ff0000',
                'border_color2': '#000000'
            },
            "farewell": {
                "enabled": False,
                "title": "Пользователь вышел :(",
                "description": "Пользователь {username} покинул наш сервер!",
                "channel": None,
                "color": "#ffffff"
            },
            "managers": [],
            "owner": None
        }
