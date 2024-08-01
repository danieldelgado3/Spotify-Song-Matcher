import os
from flask import Flask, session
from spotipy.cache_handler import FlaskSessionCacheHandler
from spotipy.oauth2 import SpotifyOAuth
from auth import sp_oauth
import config
from routes import register_routes
from database import drop_all_tables

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth.cache_handler = cache_handler

# Drop all tables when the script starts
drop_all_tables()

register_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
