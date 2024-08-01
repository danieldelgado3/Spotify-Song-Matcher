from flask import session, redirect, url_for, request
from auth import sp, sp_oauth
from database import create_table, count_unique_users, drop_all_tables, insert_tracks, get_db

user_counter = 0

def register_routes(app):

    @app.route('/')
    def home():
        html_content = """
        <html>
        <head>
            <title>Spotify Auth</title>
            <style>
                body {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background-color: #f2f2f2;
                }
                h1 {
                    margin-bottom: 20px;
                }
                form {
                    display: flex;
                    justify-content: center;
                }
                button {
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    border: none;
                    background-color: #1db954;
                    color: white;
                    border-radius: 5px;
                    transition: background-color 0.3s;
                }
                button:hover {
                    background-color: #17a445;
                }
            </style>
        </head>
        <body>
            <h1>Hello!</h1>
            <form action="/authorize" method="get">
                <button type="submit">Click here to compare your liked songs with other Spotify users!</button>
            </form>
        </body>
        </html>
        """
        return html_content


    @app.route('/authorize')
    def authorize():
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    @app.route('/callback')
    def callback():
        global user_counter
        sp_oauth.get_access_token(request.args['code'])
        user_info = sp.current_user()
        session['username'] = user_info['id']
        create_table(user_info['id'])

        user_counter = count_unique_users()
        return redirect(url_for('get_savedtracks'))

    @app.route('/add_user')
    def add_user():
        session.clear()
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    @app.route('/get_savedtracks')
    def get_savedtracks():
        if not sp_oauth.validate_token(sp_oauth.cache_handler.get_cached_token()):
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)

        username = session.get('username')
        create_table(username)

        all_saved_tracks = []
        offset = 0
        limit = 50

        while True:
            saved_tracks = sp.current_user_saved_tracks(limit=limit, offset=offset)
            if not saved_tracks['items']:
                break
            tracks_info = [(item['track']['name'], ', '.join([artist['name'] for artist in item['track']['artists']])) for item in saved_tracks['items']]
            all_saved_tracks.extend(tracks_info)
            offset += limit

        insert_tracks(username, all_saved_tracks)

        html_content = """
        <html>
        <head>
            <title>My Saved Tracks</title>
            <style>
                body {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background-color: #f2f2f2;
                }
                h1 {
                    margin-bottom: 20px;
                }
                form {
                    display: flex;
                    justify-content: center;
                    margin-bottom: 20px;
                }
                button {
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    border: none;
                    background-color: #1db954;
                    color: white;
                    border-radius: 5px;
                    transition: background-color 0.3s;
                }
                button:hover {
                    background-color: #17a445;
                }
                .track-list {
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <h1>My Saved Tracks</h1>
            <form action="/add_user" method="get">
                <button type="submit">Add User</button>
            </form>
            <div class="track-list">
                """ + "<br>".join([f"{track} - {artist}" for track, artist in all_saved_tracks]) + """
            </div>
        """

        if user_counter >= 2:
            html_content += """
            <form action="/compare_tracks" method="get">
                <button type="submit">Compare Now</button>
            </form>
            """
    
        html_content += """
        </body>
        </html>
        """
    
        return html_content


    @app.route('/compare_tracks')
    def compare_tracks():
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cur.fetchall()

            track_sets = []
            for table in tables:
                if table[0].startswith("user_"):
                    cur.execute(f"SELECT track_name, artist_name FROM {table[0]}")
                    tracks = {(row[0], row[1]) for row in cur.fetchall()}
                    track_sets.append(tracks)

            shared_tracks = set.intersection(*track_sets)
            

        html_content = """
        <html>
        <head>
            <title>Shared Tracks</title>
            <style>
                body {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                    background-color: #f2f2f2;
                }
                h1 {
                    margin-bottom: 20px;
                }
                ul {
                    list-style-type: none;
                    padding: 0;
                    text-align: center;
                }
                li {
                    margin: 5px 0;
                }
                button {
                    padding: 10px 20px;
                    font-size: 16px;
                    cursor: pointer;
                    border: none;
                    background-color: #1db954;
                    color: white;
                    border-radius: 5px;
                    transition: background-color 0.3s;
                }
                button:hover {
                    background-color: #17a445;
                }
            </style>
        </head>
        <body>
            <h1>Shared Tracks</h1>
            <ul>
        """
        for track, artist in shared_tracks:
            html_content += f"<li>{track} - {artist}</li>"
            
        html_content += """
            </ul>
        </body>
        </html>
        """
        drop_all_tables()
        return html_content


    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))
