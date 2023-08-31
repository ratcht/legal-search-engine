from flask import session
from files.obj.userobj import UserObj
from files.api.datastore import create_datastore_entry, get_datastore_entry
import bcrypt
import logging
import sys





# init logging
log = logging.getLogger('authlib')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)

def create_user(username:str, email:str, password:str):
  user = UserObj(username, email, password)
  user_value_map = user.to_map()

  create_datastore_entry(["User", email], user_value_map)

# returns a login token
def login(email: str, entered_password:str) -> str:
  user_map = get_datastore_entry("User", email)

  # verify password
  stored_password = str(user_map['PasswordEncrypted'])
  stored_password = stored_password.encode('utf-8')

  entered_password = entered_password.encode('utf-8')

  # Use conditions to compare the authenticating password with the stored one</strong>:
  if not bcrypt.checkpw(entered_password, stored_password): raise KeyError("Login: Password does not match")
  
  # Password matches. Get token
  user = UserObj(user_map['Username'], user_map['Email'], user_map['PasswordEncrypted'])

  return user
