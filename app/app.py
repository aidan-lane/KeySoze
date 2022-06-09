import os
import uuid

from dotenv import load_dotenv
from flask import Flask, render_template, session, request, redirect
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()  # take environment variables from .env

# App session config
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
Session(app)

# Store session data
caches_folder = "./.spotify_caches/"
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    """ Returns this session's storage location
    """
    return caches_folder + session.get("uuid")


scope = "user-library-read"


##########
# Routes #
##########


@app.route("/")
def index():
    if not session.get("uuid"):
        # Step 1. Visitor is unknown, give random ID
        session["uuid"] = str(uuid.uuid4())

    cache_handler = spotipy.cache_handler.CacheFileHandler(
        cache_path=session_cache_path())
    auth_manager = SpotifyOAuth(scope=scope,
                                cache_handler=cache_handler,
                                show_dialog=True)

    if request.args.get("code"):
        # Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect("/")

    token_info = auth_manager.get_cached_token()
    if token_info and not auth_manager.is_token_expired(token_info):
        # If a valid token exists, go to homepage
        access_token = token_info["access_token"]
        session["access_token"] = access_token
        return (render_template("index.html"))
    else:
        # If no valid token exists for this session, redirect user to Spotify login
        login_url = auth_manager.get_authorize_url()
        return redirect(login_url)


@app.route("/sort")
def sort():
    pass


if __name__ == "__main__":
    app.run(host="0.0.0.0")
