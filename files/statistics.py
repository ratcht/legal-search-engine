import time
from files.obj.searchobj import SearchObj, parse_search_history
from files.api.datastore import create_datastore_entry

def add_result(email:str, search_obj: SearchObj):
  create_datastore_entry(["Statistics"], {"User": email, "Prompt": search_obj.prompt, "Response": search_obj.response, "Titles": search_obj.titles, "Time Added": time.time(), "Type":search_obj.type.value}, exclude_from_indexes=["Response"])
