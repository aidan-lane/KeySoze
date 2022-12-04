import os
import json

from dotenv import load_dotenv
from flask import Flask, render_template, session, request, redirect
from flask_cors import CORS
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import app.utils as utils


load_dotenv()  # take environment variables from .env

# App session config
app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(64)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./.flask_session/"
CORS(app)


scope = "user-library-read"


##########
# Routes #
##########


@app.route("/")
def verify():
    auth_manager = SpotifyOAuth(scope=scope, show_dialog=True)

    code = request.args.get("code")
    if code:
        token_info = auth_manager.get_access_token(code)
        return render_template("index.html", data=token_info)
    else:
        login_url = auth_manager.get_authorize_url()
        return redirect(login_url)


@app.route("/sort", methods=["POST"])
def sort():
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=scope)
    sp = spotipy.Spotify(auth=request.data.decode("utf-8"), auth_manager=auth_manager)

    return utils.sort(sp, request.args.get("url"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", threaded=True)
