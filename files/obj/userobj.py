import bcrypt
import time
import jwt
import logging

class UserObj:
  def __init__(self, username:str, email:str, password:str, track_statistics=True):
    self.username = username
    self.email = email
    self.track_statistics = track_statistics
    self.password_encrypted = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')
  

  def can_search() -> bool:
    # check if user has a valid account
    pass

  def to_map(self) -> map:
    return {
      "Username": self.username,
      "Email": self.email,
      "PasswordEncrypted": self.password_encrypted ,
      "TrackStatistics":self.track_statistics
    }
  
  def create_auth_token(self) -> str:
    number_of_seconds_in_day = 24*60*60
    current_time = time.time()
    expiration_time = current_time + (7*number_of_seconds_in_day)
    encoded_jwt = jwt.encode({"exp": expiration_time}, "legal_secret_key", algorithm="HS256")
    return encoded_jwt

def parse_userobj(map: map) -> UserObj:
  username = map["Username"]
  email = map["Email"]
  password_encrypted = map["PasswordEncrypted"]
  track_statistics = map.get("TrackStatistics")
  return UserObj(username, email, password_encrypted, track_statistics)


def verify_token(token: str):
  if token is None:
    raise ValueError("No Token") 

  try:
    logging.info(f"Token: {token}")
    res = jwt.decode(token, "legal_secret_key", algorithms=["HS256"])
    return res
  except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError) as jwe:
    logging.error(jwe)
    raise ValueError("Invalid Token")
