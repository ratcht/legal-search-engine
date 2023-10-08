from google.cloud import datastore
from google.cloud.datastore.query import PropertyFilter, And
import logging
import json
from flask import session



"""This is legacy. Do not use. Just keep as reference for functions"""

"""
def fetch_config_value_by_filter(key: str):
  filters = [("Type", "=", key)]
  query = client.query(kind='Config')
  query.add_filter(filter=PropertyFilter("Type", "=", key))
  res = list(query.fetch())
  if (len(res) == 0): raise Exception("Datastore: Entity not found in database")
  if (len(res) > 1): raise Exception("Datastore: You fucked up with your keys. Multiple entities were returned")
  return res
"""

client = datastore.Client(project="legalator")

def get_user_chats(user_email, type):
  query = client.query(kind="Statistics")
  and_filter = And( 
    [
            PropertyFilter("User", "=", user_email),
            PropertyFilter("Type", "=", type),
        ]
    )
  query.add_filter(filter=and_filter)
  query.order = ["-Time Added"]
  results = list(query.fetch())
  return results

def get_user_chats_no_type(user_email):
  query = client.query(kind="Statistics")
  and_filter = And( 
    [
            PropertyFilter("User", "=", user_email),
        ]
    )
  query.add_filter(filter=and_filter)
  query.order = ["-Time Added"]
  results = list(query.fetch())
  return results


def get_count(key_type):
  query = client.query(kind="__Stat_Kind__")
  query
  result = list(query.fetch())
  for stat in result:
    if stat['kind_name'] == key_type: return stat['count']
  
  # should not be here
  raise Exception("Kind not found")

def fetch_recent_statistics(limit=5):
  query = client.query(kind="Statistics")
  query.order = ["-Time Added"]
  results = list(query.fetch(limit=limit))

  return results

def get_users(limit=None):
  query = client.query(kind="User")
  results = list(query.fetch(limit=limit))

  return results
  
def get_datastore_entry_id(key_type: str, key:int):
  keys = client.key(key_type, int(key))
  entity = client.get(key=keys)
  if (entity == None): raise KeyError(f"Datastore: Entity not found in database. KeyType: {key_type}, Key: {key}" )
  return entity

def create_datastore_entry(key_list:list, value_map, exclude_from_indexes=()):
  complete_key = client.key(*key_list)
  entity = datastore.Entity(key=complete_key, exclude_from_indexes=exclude_from_indexes)
  entity.update(
    value_map
  )
  client.put(entity)

def check_datastore_entry(key_type: str, key:str) -> bool:
  keys = client.key(key_type, key)
  entity = client.get(key=keys)
  if (entity == None): return False
  return True

def get_datastore_entry(key_type: str, key:str):
  keys = client.key(key_type, key)
  entity = client.get(key=keys)
  if (entity == None): raise KeyError(f"Datastore: Entity not found in database. KeyType: {key_type}, Key: {key}" )
  return entity


def update_datastore_entry(key_type: str, key:str, value_map:str):
  keys = client.key(key_type, key)
  entity = client.get(key=keys)
  if (entity == None): raise KeyError("Datastore: Entity not found in database")
  entity.update(
    value_map
  )
  client.put(entity)


def create_config_entry(key: str, value:str):
  complete_key = client.key("Config", key)
  entity = datastore.Entity(key=complete_key)
  entity.update(
    {
      "Value": value
    }
  )
  client.put(entity)



def update_config_value(key: str, value:str):
  keys = client.key("Config", key)
  entity = client.get(key=keys)
  if (entity == None): raise KeyError("Datastore: Entity not found in database")
  entity.update(
    {
      "Value": value
    }
  )
  client.put(entity)


def get_config_value(key:str):
  return get_config_entity_by_key(key)['Value']


def session_get_config_value(key: str) -> str:
  # key is datastore key
  if key.lower() not in session:
    session[key.lower()] = json.dumps(get_config_value(key))

  return json.loads(session[key.lower()])


def get_config_entity_by_key(key:str):
  keys = client.key("Config", key)
  entity = client.get(key=keys)
  if (entity == None): raise KeyError("Datastore: Entity not found in database")
  return entity




#try:
#  logger.info(fetch_config_value("EMBEDDING_MODEL"))
#except Exception as e:
#  logger.error(f"oh shit: {e}")

