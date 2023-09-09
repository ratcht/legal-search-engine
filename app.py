from flask import Flask, redirect, url_for, render_template, request, session, after_this_request, send_file, flash
from werkzeug.utils import secure_filename
from files.routes import admin 
from files.api.datastore import get_config_value, update_config_value, session_get_config_value, get_datastore_entry, check_datastore_entry
from files.api.openai import authenticate
from files.api.pinecone import get_pinecone_index
from files.search import search
from files.obj.userobj import UserObj, parse_userobj, verify_token
from files.obj.searchobj import SearchObj, parse_search_history
from files.obj.searchtype import SearchType
from files.obj.status import StatusObj, parse_status
from files.userhandler import login, create_user
from files.util import ComplexEncoder
from files.statistics import add_result
import google.cloud.logging
import bcrypt
import json
import os
import time
import logging
import sys
import jwt


# init logging
logging.basicConfig(level=logging.NOTSET)

# authenticate openai
OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
OPENAI_ORGANIZATION = get_config_value("OPENAI_ORGANIZATION")
authenticate(OPENAI_API_KEY, OPENAI_ORGANIZATION)

PINECONE_API_KEY = get_config_value("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = get_config_value("PINECONE_ENVIRONMENT")
PINECONE_INDEX_VALUE = get_config_value("PINECONE_INDEX")


EMBEDDING_MODEL = get_config_value("EMBEDDING_MODEL")
GPT_MODEL = get_config_value("GPT_MODEL")
GPT_USER_PROMPT = get_config_value("GPT_USER_PROMPT")


pinecone_index = get_pinecone_index(PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_VALUE)

app = Flask(__name__)
app.secret_key = "admin"


#====================================================
# Admin Routes
#====================================================

@app.route('/refresh')
def refresh_vars():
  return admin.refresh_vars()

@app.route('/gcl')
def gcl():
  return admin.gcl()

@app.route('/statistics/enable')
def statistics_enable():
  session["track_statistics"] = True
  return "<html><p>Tracking Statistics...</p></html>"

@app.route('/statistics/disable')
def statistics_disable():
  session["track_statistics"] = False
  return "<html><p>Stopped Tracking Statistics...</p></html>"

#====================================================
# Search Routes
#====================================================

@app.route("/search/query", methods=["POST"])
def chat():  

    # Check if user is signed in
  try:
    token = session.get("token")
    res = verify_token(token)
  except ValueError as ve:
    logging.error(ve)
    return redirect(url_for("login_page"))
  
  # Get User
  user = parse_userobj(session["user"])

  if not user.can_search():
    return redirect(url_for("index"))

  # Get chat input
  logging.info("In /search/query")
  search_input = request.form["searchInput"]
  search_type = SearchType(request.form["searchType"])
  logging.info(f"Search Type: {search_type.value}")

  # Send chat to GPT
  try:
    search_response, search_titles, search_excerpts = search(search_input, search_type, pinecone_index, GPT_MODEL, EMBEDDING_MODEL, GPT_USER_PROMPT)
  except Exception as e:
    print("Error Thrown")
    session["error"] = json.dumps(StatusObj(500, f"Something happened! Please retry. Exception: {e}"), cls=ComplexEncoder)
    return session["error"]

  logging.info(f"Titles Found: {search_titles}")

  search_obj = SearchObj(search_input, search_response, search_titles)
  status = StatusObj(200)

  # set result in session
  session["search"] = search_obj.jsonify()

  # update statistics
  if session["track_statistics"]:
    logging.info("Updating Statistics...")
    print(session["track_statistics"])

    add_result(user.email, search_obj)

  return redirect(url_for("search_page", search_type=search_type.value))


@app.route("/search/history", methods=["GET"])
def search_history():
    # Check if user is signed in
  try:
    token = session.get("token")
    res = verify_token(token)
  except ValueError as ve:
    logging.error(ve)
    return redirect(url_for("login_page"))
  
  # Get User
  user = parse_userobj(session["user"])

  if not user.can_search():
    return redirect(url_for("index"))

  logging.info(f'Search: {session["search"]}')
  return render_template("partials/search-partial.html", loaded_search_history=parse_search_history(json.loads(session["search"])))


@app.route("/search/clear", methods=["GET"])
def clear():  
  logging.info("In Search Page")

  # Check if user is signed in
  try:
    token = session.get("token")
    res = verify_token(token)
  except ValueError as ve:
    logging.error(ve)
    return redirect(url_for("login_page"))
  
  # Get User
  user = parse_userobj(session["user"])

  if not user.can_search():
    return redirect(url_for("index"))

  # set session if not set
  if "search" in session:
    session.pop("search")

  return redirect(url_for("search_page"))


@app.route("/search/page", methods=["GET"])
def search_page():  
  logging.info("In Search Page")

  # Check if user is signed in
  try:
    token = session.get("token")
    res = verify_token(token)
  except ValueError as ve:
    logging.error(ve)
    return redirect(url_for("login_page"))
  
  user = parse_userobj(session["user"])

  if not user.can_search():
    return redirect(url_for("index"))

  
  search_type_arg = request.args.get("search_type")
  search_type = SearchType(search_type_arg) if search_type_arg else SearchType.CASE_LAW


  # if previous message and query already exists
  if "search" in session:
    search_obj = session["search"]
    logging.info(search_obj)
    return render_template("search.html", search_obj = search_obj, search_type=search_type, user = user)


  return render_template("search.html", search_type=search_type, user = user)


#====================================================
# User Routes
#====================================================

@app.route("/user/signout", methods=["GET"])
def sign_out():  
  logging.info("Signing out...")

  session.clear()
  return redirect(url_for("index"))


@app.route("/user/login/page", methods=["GET"])
def login_page():  
  logging.info("In Login Page")

  # if user already logged in, redirect to search
  try:
    token = session.get("token")
    res = verify_token(token)
    logging.info("Already Signed In...")
    return redirect(url_for("/search/page"))
  except ValueError as ve:
    pass

  return render_template("login.html")



@app.route("/user/login/post", methods=["POST"])
def login_post():  
  logging.info("Login Post")

  try:
    token = session.get("token")
    res = verify_token(token)
    logging.info("Already Signed In...")
    return redirect(url_for("/search/page"))
  except ValueError as ve:
    pass

  email = request.form["emailInput"]
  password = request.form["passwordInput"]

  try:
    user: UserObj = login(email, password)
    token = user.create_auth_token()
  except KeyError as ke:
    logging.error(ke)
    return redirect(url_for('login_page', error_message = "Email or Password is incorrect. Please try again."))
  
  session['user'] = user.to_map()
  session['token'] = token
  session['track_statistics'] = user.track_statistics

  return redirect(url_for('search_page'))


@app.route("/user/signup/page", methods=["GET"])
def signup_page():  
  logging.info("In Signup Page")

  # if user already logged in, redirect to search
  try:
    token = session.get("token")
    res = verify_token(token)
    logging.info("Already Signed In...")
    return redirect(url_for("/search/page"))
  except ValueError as ve:
    pass

  return render_template("signup.html")


@app.route("/user/signup/post", methods=["POST"])
def signup_post():  
  logging.info("Signup Post")

  try:
    token = session.get("token")
    res = verify_token(token)
    logging.info("Already Signed In...")
    return redirect(url_for("/search/page"))
  except ValueError as ve:
    pass

  username = request.form["usernameInput"]
  email = request.form["emailInput"]
  password = request.form["passwordInput"]

  # Check if username already exists
  is_exists = check_datastore_entry("User", email)
  if is_exists: return redirect(url_for("signup_page", error_message="Account with email already exists"))

  create_user(username, email, password)

  return redirect(url_for('login_page'))

#====================================================
# Home Routes
#====================================================

@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def index():  
  logging.info("In Index Page")

  # Check if user is signed in
  try:
    token = session.get("token")
    res = verify_token(token)
    signed_in = True
    user = parse_userobj(session.get("user"))
    logging.info("Already Signed In")
  except ValueError as ve:
    logging.error(ve)
    signed_in = False
    user = None
    logging.info("Not Signed In")
  


  return render_template("index.html", signed_in = signed_in, user = user)


if __name__ == "__main__":
  # webbrowser.open('http://127.0.0.1:8000')  # Go to example.com
  # set upload folder
  app.config["SESSION_TYPE"] = 'filesystem'

  # run app
  app.run(port=8000, debug=True)