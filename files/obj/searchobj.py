import json

class SearchObj:
  def __init__(self, prompt, response, titles, excerpts=""):
    self.prompt = prompt
    self.response = response
    self.titles = titles
    self.excerpts = excerpts
  
  def jsonify(self):
    return dict(prompt = self.prompt, response=self.response, titles = self.titles, excerpts = self.excerpts) 
  

def parse_search_history(json_obj):
  search_history = []
  for search_obj_json in json_obj:
    search_obj = SearchObj(search_obj_json["prompt"], search_obj_json["response"])
    search_history.append(search_obj)
  return search_history

