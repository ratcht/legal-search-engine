from flask import Flask, session, redirect, url_for
from files.api.openai import authenticate
from files.api.datastore import get_config_value, update_config_value, session_get_config_value
import google.cloud.logging
import logging
import json


def refresh_vars():
  logging.info("/refresh")
  logging.warning('Reauthenticating OpenAI...')
  OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
  session['openai_api_key'] = OPENAI_API_KEY
  authenticate(OPENAI_API_KEY)

  session['outline_prompt'] = json.dumps(get_config_value("OUTLINE_PROMPT"))
  session['outline_context'] = json.dumps(get_config_value("OUTLINE_CONTEXT"))

  return redirect(url_for('index'))

def gcl():
  logging.info("/gcl")
  client = google.cloud.logging.Client()
  client.get_default_handler()
  client.setup_logging()
  return '<html><body>Logging was set up</body></html>'