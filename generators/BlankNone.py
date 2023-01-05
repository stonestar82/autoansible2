import yaml, os, re
from yaml.representer import Representer
from yaml.dumper import Dumper
from jinja2.runtime import Undefined

def getExcelSheetValue(excel, config):
  """
  엑셀에서 원하는 정보 1개를 읽어옴
  """
  v = excel[config["sheet"]][config["p"]].value
  
  if v == "" or not v:
    v = config["defaultValue"]

  return v

class BlankNone(Representer):
  """Print None as blank when used as context manager"""
  def represent_none(self, *_):
    return self.represent_scalar(u'tag:yaml.org,2002:null', u'')

  def __enter__(self):
    self.prior = Dumper.yaml_representers[type(None)]
    yaml.add_representer(type(None), self.represent_none)

  def __exit__(self, exc_type, exc_val, exc_tb):
    Dumper.yaml_representers[type(None)] = self.prior
    
    
def convert_dicts(dictionary, primary_key="name", secondary_key=None):
    
  if not isinstance(dictionary, (dict, list)) or os.environ.get('AVD_DISABLE_CONVERT_DICTS'):
    # Not a dictionary/list, return the original
    return dictionary
  elif isinstance(dictionary, list):
    output = []
    for element in dictionary:
      if not isinstance(element, dict):
        item = {}
        item.update({primary_key: element})
        output.append(item)
      else:
        output.append(element)
    return output
  else:
    output = []
    for key in dictionary:
      if not isinstance(dictionary[key], dict):
        # Not a nested dictionary, add secondary key for the values if secondary key is provided
        if secondary_key is not None:
          item = {}
          item.update({primary_key: key})
          item.update({secondary_key: dictionary[key]})
          output.append(item)
        else:
          # Catch cornercase where dictionary value is not a dict because of old data models
          # Ex <key>: "none" or <key>: null or <key>: "" will all be overwritten with {<primary_key>: <key>}
          output.append({primary_key: key})
      else:
        item = dictionary[key].copy()
        item.update({primary_key: key})
        output.append(item)
    return output
  
def convert(text):
  return int(text) if text.isdigit() else text.lower()
  
def natural_sort(iterable, sort_key=None):
  if isinstance(iterable, Undefined) or iterable is None:
    return []

  def alphanum_key(key):
    if sort_key is not None and isinstance(key, dict):
      return [convert(c) for c in re.split('([0-9]+)', str(key.get(sort_key, key)))]
    else:
      return [convert(c) for c in re.split('([0-9]+)', str(key))]

  return sorted(iterable, key=alphanum_key)