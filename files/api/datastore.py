from google.cloud import datastore
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

def create_datastore_entry(key_list:list, value_map):
  complete_key = client.key(*key_list)
  entity = datastore.Entity(key=complete_key)
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

