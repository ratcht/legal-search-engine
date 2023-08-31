import time
from files.obj.searchobj import SearchObj, parse_search_history
from files.api.datastore import create_datastore_entry

def add_result(email:str, search_obj: SearchObj):
  create_datastore_entry(["Statistics"], {"User": email, "Prompt": search_obj.prompt, "Time Added": time.time()})
