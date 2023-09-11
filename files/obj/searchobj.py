import json
from files.obj.searchtype import SearchType

class SearchObj:
  def __init__(self, prompt, response, titles, type: SearchType, excerpts=""):
    self.prompt = prompt
    self.type = type
    self.response = response
    self.titles = titles
    self.excerpts = excerpts
  
  def jsonify(self):
    return dict(prompt = self.prompt, response=self.response, titles = self.titles, type=self.type.value, excerpts = self.excerpts) 
  

def parse_search_history(json_obj):
  search_history = []
  for search_obj_json in json_obj:
    search_obj = SearchObj(search_obj_json["prompt"], search_obj_json["response"], search_obj_json["titles"], SearchType(search_obj_json["type"]))
    search_history.append(search_obj)
  return search_history

