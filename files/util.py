import json 

class ComplexEncoder(json.JSONEncoder):
  def default(self, obj):
    if hasattr(obj,'jsonify'):
      return obj.jsonify()
    else:
      return json.JSONEncoder.default(self, obj)

def filter_list(list_to_filter: list) -> list:
  return list(dict.fromkeys(list_to_filter))