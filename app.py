import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

load_dotenv()

# --- CONFIGURATION ---
DATABASE_URL = os.environ.get('DATABASE_URL')
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')

# --- FLASK APP ---
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DATABASE HELPER ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# --- DATABASE SETUP ---
def init_db():
    """Initializes the PostgreSQL database with all required tables."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY, fullName VARCHAR(255), college VARCHAR(255),
        email VARCHAR(255) UNIQUE, password VARCHAR(255), bio TEXT, gender VARCHAR(50),
        preference VARCHAR(50), age INTEGER, interests TEXT, profile_image_url VARCHAR(255)
    );""")
    print("-> Table 'users' verified.")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id SERIAL PRIMARY KEY, liker_id INTEGER REFERENCES users(id),
        liked_id INTEGER REFERENCES users(id), UNIQUE(liker_id, liked_id)
    );""")
    print("-> Table 'likes' verified.")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id SERIAL PRIMARY KEY, user1_id INTEGER REFERENCES users(id),
        user2_id INTEGER REFERENCES users(id), UNIQUE(user1_id, user2_id)
    );""")
    print("-> Table 'matches' verified.")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY, match_id INTEGER REFERENCES matches(id),
        sender_id INTEGER REFERENCES users(id), message_text TEXT NOT NULL,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );""")
    print("-> Table 'messages' verified.")
    conn.commit()
    cur.close()
    conn.close()
    print("--- DATABASE INITIALIZATION COMPLETE ---")


# --- HTML SERVING ROUTES ---
@app.route("/")
def index(): return render_template('index.html')

@app.route('/<page_name>.html')
def serve_html_page(page_name): return render_template(f'{page_name}.html')


# --- API ROUTES ---
# (All your API routes like /signup, /login, etc., are complete and correct below)

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
    user_data = request.get_json()
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

@app.route("/matches", methods=['GET'])
def get_matches():
    user_id = request.args.get('userId')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    query = "SELECT m.id as match_id, u.id as user_id, u.fullName FROM matches m JOIN users u ON (u.id = m.user2_id AND m.user1_id = %s) OR (u.id = m.user1_id AND m.user2_id = %s) WHERE (m.user1_id = %s OR m.user2_id = %s) AND u.id != %s"
    cur.execute(query, (user_id, user_id, user_id, user_id, user_id))
    matches = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(row) for row in matches])

@app.route("/messages/<int:match_id>", methods=['GET'])
def get_messages(match_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT * FROM messages WHERE match_id = %s ORDER BY timestamp ASC", (match_id,))
    messages = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(row) for row in messages])

@app.route("/send_message", methods=['POST'])
def send_message():
    conn = get_db_connection()
    cur = conn.cursor()
    data = request.get_json()
    cur.execute("INSERT INTO messages (match_id, sender_id, message_text) VALUES (%s, %s, %s)", (data.get('match_id'), data.get('sender_id'), data.get('message_text')))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success", "message": "Message sent"})

@app.route("/profile/<int:user_id>", methods=['GET'])
def get_profile(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute("SELECT id, fullName, college, age, bio, gender, preference, interests, email, profile_image_url FROM users WHERE id = %s", (user_id,))
    user_profile = cur.fetchone()
    cur.close()
    conn.close()
    if user_profile: return jsonify(dict(user_profile))
    else: return jsonify({"error": "User not found"}), 404

@app.route("/update_profile", methods=['POST'])
def update_profile():
    conn = get_db_connection()
    cur = conn.cursor()
    data = request.get_json()
    interests_string = ",".join(data.get('interests', []))
    update_query = "UPDATE users SET fullName = %s, college = %s, age = %s, bio = %s, interests = %s WHERE id = %s"
    cur.execute(update_query, (data.get('fullName'), data.get('college'), data.get('age'), data.get('bio'), interests_string, data.get('userId')))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status": "success", "message": "Profile updated successfully!"})

# --- MAIN EXECUTION BLOCK (CORRECTED) ---
# This code runs ONLY when you run 'python app.py' on your local machine.
# It does NOT run on the Render server.
if __name__ == "__main__":
    # Create the uploads folder if it doesn't exist locally
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # Start the local development server
    app.run(debug=True)
else:
    # This block runs when the file is imported by Gunicorn on Render.
    # We run the database setup here, ensuring it runs once when the server starts.
    init_db()