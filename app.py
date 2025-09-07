import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

load_dotenv()

DATABASE_URL = os.environ.get('DATABASE_URL')
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, fullName VARCHAR(255), college VARCHAR(255), email VARCHAR(255) UNIQUE, password VARCHAR(255), bio TEXT, gender VARCHAR(50), preference VARCHAR(50), age INTEGER, interests TEXT, profile_image_url VARCHAR(255));")
    cur.execute("CREATE TABLE IF NOT EXISTS likes (id SERIAL PRIMARY KEY, liker_id INTEGER REFERENCES users(id), liked_id INTEGER REFERENCES users(id), UNIQUE(liker_id, liked_id));")
    cur.execute("CREATE TABLE IF NOT EXISTS matches (id SERIAL PRIMARY KEY, user1_id INTEGER REFERENCES users(id), user2_id INTEGER REFERENCES users(id), UNIQUE(user1_id, user2_id));")
    cur.execute("CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, match_id INTEGER REFERENCES matches(id), sender_id INTEGER REFERENCES users(id), message_text TEXT NOT NULL, timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP);")
    conn.commit()
    cur.close()
    conn.close()
    print("--- DATABASE INITIALIZATION COMPLETE ---")

@app.before_first_request
def create_tables():
    print("--- RUNNING FIRST REQUEST SETUP ---")
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    init_db()
    print("--- FIRST REQUEST SETUP COMPLETE ---")

@app.route("/")
def index(): return render_template('index.html')

@app.route('/<page_name>.html')
def serve_html_page(page_name): return render_template(f'{page_name}.html')

# ... ALL YOUR OTHER API ROUTES GO HERE ...
# (The following is the complete set of routes for clarity)
@app.route("/signup", methods=['POST'])
def signup():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        full_name = request.form.get('fullName')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        insert_query = "INSERT INTO users (fullName, college, email, password, bio, gender, preference, age, interests) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id"
        cur.execute(insert_query, (full_name, request.form.get('college'), request.form.get('email'), hashed_password, request.form.get('bio'), request.form.get('gender'), request.form.get('preference'), request.form.get('age'), request.form.get('interests')))
        new_user_id = cur.fetchone()[0]
        conn.commit()
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            new_filename = f"user_{new_user_id}_{secure_filename(file.filename)}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
            profile_image_url = f"/static/uploads/{new_filename}"
            cur.execute("UPDATE users SET profile_image_url = %s WHERE id = %s", (profile_image_url, new_user_id))
            conn.commit()
        return jsonify({"status": "success", "message": f"Welcome, {full_name}!", "user": {"id": new_user_id, "fullName": full_name}})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route("/login", methods=['POST'])
def login():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    user__data = request.get_json()
    email = user_data.get('email'); password = user_data.get('password')
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and check_password_hash(user['password'], password):
        user_data_response = {"id": user['id'], "fullName": user['fullname']}
        return jsonify({"status": "success", "message": f"Welcome back, {user['fullname']}!", "user": user_data_response})
    else: return jsonify({"status": "error", "message": "Invalid email or password."}), 401

@app.route("/users", methods=['GET'])
def get_users():
    logged_in_user_id = request.args.get('userId')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT preference FROM users WHERE id = %s", (logged_in_user_id,))
    user = cur.fetchone()
    user_preference = user['preference'] if user else 'Everyone'
    query = "SELECT id, fullName, college, age, bio, gender, interests, profile_image_url FROM users WHERE id != %s"
    params = [logged_in_user_id]
    if user_preference == 'Men': query += " AND gender = 'Man'"
    elif user_preference == 'Women': query += " AND gender = 'Woman'"
    cur.execute(query, params)
    users = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(row) for row in users])

@app.route("/like", methods=['POST'])
def like_user():
    conn = get_db_connection()
    cur = conn.cursor()
    data = request.get_json()
    liker_id = data.get('liker_id'); liked_id = data.get('liked_id')
    try:
        cur.execute("INSERT INTO likes (liker_id, liked_id) VALUES (%s, %s)", (liker_id, liked_id))
        cur.execute("SELECT * FROM likes WHERE liker_id = %s AND liked_id = %s", (liked_id, liker_id))
        match_record = cur.fetchone()
        match_created = False
        if match_record:
            user1 = min(int(liker_id), int(liked_id)); user2 = max(int(liker_id), int(liked_id))
            try:
                cur.execute("INSERT INTO matches (user1_id, user2_id) VALUES (%s, %s)", (user1, user2))
                match_created = True
            except: pass
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return jsonify({"status": "success", "match": match_created})

# ... (the rest of your routes for /matches, /messages, /profile, /update_profile) ...

if __name__ == "__main__":
    app.run(debug=True)