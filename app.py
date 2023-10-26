from flask import Flask, redirect, url_for, render_template, request, session, after_this_request, send_file, flash
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from files.routes import admin 
from files.api.datastore import *
from files.api.pinecone import *
from files.api.openai import *
from files.search import search, load_history
from files.obj.userobj import *
from files.obj.searchobj import *
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
logging.basicConfig(level=logging.ERROR)

# authenticate openai
OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
OPENAI_ORGANIZATION = get_config_value("OPENAI_ORGANIZATION")
authenticate(OPENAI_API_KEY, OPENAI_ORGANIZATION)

PINECONE_API_KEY = get_config_value("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = get_config_value("PINECONE_ENVIRONMENT")
PINECONE_INDEX_VALUE = get_config_value("PINECONE_INDEX_VALUE")


EMBEDDING_MODEL = get_config_value("EMBEDDING_MODEL")
GPT_MODEL = get_config_value("GPT_MODEL")
GPT_USER_PROMPT = get_config_value("GPT_USER_PROMPT")


pinecone_index = get_pinecone_index(PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_VALUE)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
app.config['APPLICATION_ROOT'] = '/'
app.config['PREFERRED_URL_SCHEME'] = 'https'

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
  data = request.get_json()
  search_input = data["prompt"]
  search_type = SearchType(data["type"])
  logging.info(f"Search Type: {search_type.value}")

  # get previous user chats
  prev_chats: list[SearchObj] = load_history(get_user_chats(user.email, search_type.value), cut=3)

  # Send chat to GPT
  try:
    search_response, search_titles, search_excerpts = search(search_input, search_type, pinecone_index, prev_chats, GPT_MODEL, EMBEDDING_MODEL, GPT_USER_PROMPT)
  except Exception as e:
    print("Error Thrown")
    session["error"] = json.dumps(StatusObj(500, f"Something happened! Please retry. Exception: {e}"), cls=ComplexEncoder)
    return session["error"]

  logging.info(f"Titles Found: {search_titles}")

  search_obj = SearchObj(search_input, search_response, search_titles[0:3], type=search_type)
  status = StatusObj(200)

  # set result in session
  session["search"] = search_obj.jsonify()

  # update statistics
  if session["track_statistics"]:
    logging.info("Updating Statistics...")
    print(session["track_statistics"])

    add_result(user.email, search_obj)
  
  return render_template("partials/searchrow.html", search_res = [search_obj])


@app.route("/search/list", methods=["GET"])
def chat_list():
  try:
    token = session.get("token")
    res = verify_token(token)
  except ValueError as ve:
    logging.error(ve)
    return redirect(url_for("login_page"))
  
  # Get User
  user = parse_userobj(session["user"])

  if not user.can_search(): return redirect(url_for("index"))

  if request.args.get("cut") == None: cut = 5
  else: cut = int(request.args.get("cut"))

  if request.args.get("start") == None: start = 0
  else: start = int(request.args.get("start"))
  
  type = request.args.get("type")

  res = get_user_chats(user.email, type)

  chats = load_history(res, cut=cut, start=start)

  return render_template("partials/searchrow.html", search_res=list(reversed(chats)))


@app.route("/search/clear", methods=["GET"])
def clear():  
  logging.info("In Search Page")

  # check if user is signed in
  try:
    token = session.get("token")
    res = verify_token(token)
  except ValueError as ve:
    logging.error(ve)
    return redirect(url_for("login_page"))
  
  # get User
  user = parse_userobj(session["user"])

  if not user.can_search(): return redirect(url_for("index"))

  # reset session
  if "search" in session: session.pop("search")

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


@app.route("/user/profile", methods=["GET"])
def profile():  
  logging.info("In Profile Page")

  # Check if user is signed in
  try:
    token = session.get("token")
    res = verify_token(token)
  except ValueError as ve:
    logging.error(ve)
    return redirect(url_for("login_page"))
  
  user = parse_userobj(session["user"])

  if not user.can_search(): return redirect(url_for("index"))

  return render_template("profile.html", user = user)

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
    return redirect(url_for("search_page"))
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
    return redirect(url_for("search_page"))
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
    return redirect(url_for("search_page"))
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
    return redirect(url_for("search_page"))
  except ValueError as ve:
    pass

  username = request.form["usernameInput"]
  email = request.form["emailInput"]
  password = request.form["passwordInput"]

  # Check if username already exists
  is_exists = check_datastore_entry("User", email)
  if is_exists: return redirect(url_for("signup_page", error_message="Account with email already exists"))

  create_user(username, email, password)

  return redirect(url_for('approve_page'))


@app.route("/user/approve", methods=["GET"])
def approve_page():  
  logging.info("approve page")


  return render_template("approve.html")

#=============
#Admin
#=============


@app.route("/1234/admin/config/page", methods=["GET"])
def admin_config_page():  
  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))
  PINECONE_API_KEY = get_config_value("PINECONE_API_KEY")
  GPT_PROMPT = get_config_value("GPT_USER_PROMPT")
  OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
  GPT_MODEL = get_config_value("GPT_MODEL")
  ADMIN_PASSWORD = get_config_value("ADMIN_PASSWORD")


  return render_template("config.html", pinecone_api = PINECONE_API_KEY, openai_api = OPENAI_API_KEY, gpt_prompt = GPT_PROMPT, gpt_model = GPT_MODEL, admin_password = ADMIN_PASSWORD)


@app.route("/1234/admin/config/update", methods=["POST"])
def admin_config_update():
  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))
  gptPrompt = request.form['gptPrompt']
  pineconeAPI = request.form['pineconeAPI']
  gptModel = request.form['gptModel']
  openaiAPI = request.form['openaiAPI']
  adminPassword = request.form['adminPassword']

  update_config_value("GPT_USER_PROMPT", gptPrompt)
  update_config_value("GPT_MODEL", gptModel)
  update_config_value("PINECONE_API_KEY", pineconeAPI)
  update_config_value("OPENAI_API_KEY", openaiAPI)
  update_config_value("ADMIN_PASSWORD", adminPassword)

  return redirect(url_for('admin_config_page'))



@app.route("/1234/admin/users/setpaid", methods=["GET"])
def admin_set_paid():  
  logging.info("Users List Page")
  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))
  user_email = request.args.get("email")

  update_datastore_entry("User", user_email, {"Paid": True})

  return redirect(url_for("admin_users_list"))

@app.route("/1234/admin/users", methods=["GET"])
def admin_users_page():  
  logging.info("Users Page")
  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))
  
  email = request.args.get("email")

  user = get_datastore_entry("User", email)
  user_obj = UserStatObj(username = user["Username"], email = user["Email"], paid = user["Paid"]) 
  

  entities = get_user_chats_no_type(email)
  search_objs = [StatObj(prompt=entity["Prompt"], response=entity["Response"], titles=entity["Titles"], time=entity["Time Added"], type=entity["Type"], user=entity["User"], id=entity.id) for entity in entities]




  return render_template("userdetailed.html", user_obj = user_obj, search_objs = search_objs)

@app.route("/1234/admin/users/list", methods=["GET"])
def admin_users_list():  
  logging.info("Users List Page")
  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))
  entities = get_users()
  user_objs = [UserStatObj(username = entity["Username"], email = entity["Email"], paid = entity["Paid"]) for entity in entities]


  return render_template("userlist.html", user_objs = user_objs)


@app.route("/1234/admin/statistics/detailed", methods=["GET"])
def admin_detailed_stat():  
  logging.info("In Statistics Page")
  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))

  id = int(request.args.get("id"))

  entity = get_datastore_entry_id("Statistics", id)
  search_obj = StatObj(prompt=entity["Prompt"], response=entity["Response"], titles=entity["Titles"], time=entity["Time Added"], type=entity["Type"], user=entity["User"], id=entity.id)
  print(search_obj)

  return render_template("detailed.html", search_obj=search_obj)


@app.route("/1234/admin/statistics/view", methods=["GET"])
def admin_statistics_view():  
  logging.info("In Statistics Page")

  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))
  
  top_searches = fetch_recent_statistics(limit=50)
  
  top_searches_parsed = [StatObj(prompt=entity["Prompt"], response=entity["Response"], titles=entity["Titles"], time=entity["Time Added"], type=entity["Type"], user=entity["User"], id=entity.id) for entity in top_searches]

  return render_template("statistics.html", recent_search_objs=top_searches_parsed)

@app.route("/1234/admin", methods=["GET"])
def admin_index():  
  logging.info("In Index Page")

  if session.get("admin_authed") != True:
    return redirect(url_for('admin_login'))

  # search queries
  top_searches = fetch_recent_statistics(limit=10)
  top_searches_parsed = [StatObj(prompt=entity["Prompt"], response=entity["Response"], titles=entity["Titles"], time=entity["Time Added"], type=entity["Type"], user=entity["User"], id=entity.id) for entity in top_searches]


  # get statistics

  # get count
  user_count = get_count("User")
  query_count = get_count("Statistics")

  pinecone_count = get_starting_id(pinecone_index)

  return render_template("admin.html", recent_search_objs=top_searches_parsed, query_count = query_count, user_count=user_count, database_count = pinecone_count)



@app.route("/1234/admin/login", methods=["GET"])
def admin_login():  
  logging.info("In Login Page")

  if session.get("admin_authed") == True:
    return redirect(url_for('admin_index'))
  
  return render_template("password.html")

@app.route("/1234/admin/verify", methods=["POST"])
def admin_verify():  
  logging.info("In Login Page")

  if session.get("admin_authed") == True:
    return redirect(url_for('admin_index'))

  password = get_config_value("ADMIN_PASSWORD")

  entered_password = request.form["password"]

  if password == entered_password:
    session["admin_authed"] = True
    return redirect(url_for('admin_index'))
  
  
  return redirect(url_for('admin_login'))

#====================================================
# Home Routes
#====================================================

@app.route("/1234/pages/contact", methods=["GET"])
def contact_page():  
  logging.info("In Contact Page")

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

  #return redirect(url_for("login_page"))
  return render_template("contact.html", signed_in = signed_in, user = user)


@app.route("/1234/pages/pricing", methods=["GET"])
def pricing_page():  
  logging.info("In Pricing Page")

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

  #return redirect(url_for("login_page"))
  return render_template("pricing.html", signed_in = signed_in, user = user)


@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def temp_index():
  return redirect(url_for('login_page'))

@app.route("/1234", methods=["GET"])
@app.route("/1234/home", methods=["GET"])
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
  

  #return redirect(url_for("login_page"))
  return render_template("index.html", signed_in = signed_in, user = user)


@app.before_request
def before_request():
  if not request.is_secure:
    url = request.url.replace('http://', 'https://', 1)
    code = 301
    return redirect(url, code=code)


if __name__ == "__main__":
  # webbrowser.open('http://127.0.0.1:8000')  # Go to example.com
  # set upload folder
  app.config["SESSION_TYPE"] = 'filesystem'
  app.config['APPLICATION_ROOT'] = '/'
  app.config['PREFERRED_URL_SCHEME'] = 'https'



  # run app
  app.run(port=8000, debug=True)