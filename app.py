import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- CONFIGURATION ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# --- FLASK APP ---
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- HELPER FUNCTION ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fullName TEXT NOT NULL, college TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, bio TEXT, gender TEXT,
        preference TEXT, age INTEGER, interests TEXT, profile_image_url TEXT
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, liker_id INTEGER NOT NULL, liked_id INTEGER NOT NULL,
        FOREIGN KEY (liker_id) REFERENCES users(id), FOREIGN KEY (liked_id) REFERENCES users(id),
        UNIQUE(liker_id, liked_id)
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user1_id INTEGER NOT NULL, user2_id INTEGER NOT NULL,
        FOREIGN KEY (user1_id) REFERENCES users(id), FOREIGN KEY (user2_id) REFERENCES users(id),
        UNIQUE(user1_id, user2_id)
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, match_id INTEGER NOT NULL, sender_id INTEGER NOT NULL,
        message_text TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES matches(id), FOREIGN KEY (sender_id) REFERENCES users(id)
    );""")
    conn.commit()
    conn.close()

# --- HTML SERVING ROUTES ---
@app.route("/")
def index(): return render_template('index.html')

@app.route('/<page_name>.html')
def serve_html_page(page_name): return render_template(f'{page_name}.html')

# --- API ROUTES ---

@app.route("/signup", methods=['POST'])
def signup():
    try:
        full_name = request.form.get('fullName')
        college = request.form.get('college')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('bio')
        gender = request.form.get('gender')
        preference = request.form.get('preference')
        age = request.form.get('age')
        interests_string = request.form.get('interests')

        if not all([full_name, college, email, password, age, gender]):
            return jsonify({"status": "error", "message": "Missing required fields."}), 400

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        insert_query = "INSERT INTO users (fullName, college, email, password, bio, gender, preference, age, interests) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cursor.execute(insert_query, (full_name, college, email, hashed_password, bio, gender, preference, age, interests_string))
        new_user_id = cursor.lastrowid
        conn.commit()

        profile_image_url = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                new_filename = f"user_{new_user_id}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                profile_image_url = f"/static/uploads/{new_filename}"

                cursor.execute("UPDATE users SET profile_image_url = ? WHERE id = ?", (profile_image_url, new_user_id))
                conn.commit()
        
        conn.close()
        
        user_data_response = {"id": new_user_id, "fullName": full_name}
        return jsonify({"status": "success", "message": f"Welcome, {full_name}! Your account has been created.", "user": user_data_response})

    except Exception as e:
        print(f"!!! SERVER CRASHED on /signup: {e}")
        return jsonify({"status": "error", "message": "A server error occurred."}), 500

@app.route("/login", methods=['POST'])
def login():
    user_data = request.get_json()
    email = user_data.get('email'); password = user_data.get('password')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        user_data_response = {"id": user['id'], "fullName": user['fullName']}
        return jsonify({"status": "success", "message": f"Welcome back, {user['fullName']}!", "user": user_data_response})
    else: return jsonify({"status": "error", "message": "Invalid email or password."}), 401

@app.route("/users", methods=['GET'])
def get_users():
    logged_in_user_id = request.args.get('userId')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT preference FROM users WHERE id = ?", (logged_in_user_id,))
    user = cursor.fetchone()
    user_preference = user['preference'] if user else 'Everyone'
    query = "SELECT id, fullName, college, age, bio, gender, interests, profile_image_url FROM users WHERE id != ?"
    params = [logged_in_user_id]
    if user_preference == 'Men': query += " AND gender = 'Man'"
    elif user_preference == 'Women': query += " AND gender = 'Woman'"
    cursor.execute(query, params)
    users = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in users])

@app.route("/like", methods=['POST'])
def like_user():
    data = request.get_json()
    liker_id = data.get('liker_id'); liked_id = data.get('liked_id')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO likes (liker_id, liked_id) VALUES (?, ?)", (liker_id, liked_id))
        cursor.execute("SELECT * FROM likes WHERE liker_id = ? AND liked_id = ?", (liked_id, liker_id))
        match_record = cursor.fetchone()
        match_created = False
        if match_record:
            user1 = min(int(liker_id), int(liked_id)); user2 = max(int(liker_id), int(liked_id))
            try:
                cursor.execute("INSERT INTO matches (user1_id, user2_id) VALUES (?, ?)", (user1, user2))
                match_created = True
            except sqlite3.IntegrityError:
                match_created = True
        conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "success", "match": match_created})

@app.route("/matches", methods=['GET'])
def get_matches():
    user_id = request.args.get('userId')
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT m.id as match_id, u.id as user_id, u.fullName FROM matches m JOIN users u ON (u.id = m.user2_id AND m.user1_id = ?) OR (u.id = m.user1_id AND m.user2_id = ?) WHERE (m.user1_id = ? OR m.user2_id = ?) AND u.id != ?"
    cursor.execute(query, (user_id, user_id, user_id, user_id, user_id))
    matches = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in matches])

@app.route("/messages/<int:match_id>", methods=['GET'])
def get_messages(match_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE match_id = ? ORDER BY timestamp ASC", (match_id,))
    messages = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in messages])

@app.route("/send_message", methods=['POST'])
def send_message():
    data = request.get_json()
    match_id = data.get('match_id'); sender_id = data.get('sender_id'); message_text = data.get('message_text')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (match_id, sender_id, message_text) VALUES (?, ?, ?)", (match_id, sender_id, message_text))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Message sent"})

@app.route("/profile/<int:user_id>", methods=['GET'])
def get_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT id, fullName, college, age, bio, gender, preference, interests, email, profile_image_url FROM users WHERE id = ?"
    cursor.execute(query, (user_id,))
    user_profile = cursor.fetchone()
    conn.close()
    if user_profile:
        return jsonify(dict(user_profile))
    else:
        return jsonify({"error": "User not found"}), 404

@app.route("/update_profile", methods=['POST'])
def update_profile():
    data = request.get_json()
    user_id = data.get('userId')
    full_name = data.get('fullName'); college = data.get('college'); age = data.get('age')
    bio = data.get('bio'); interests_string = ",".join(data.get('interests', []))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    update_query = "UPDATE users SET fullName = ?, college = ?, age = ?, bio = ?, interests = ? WHERE id = ?"
    cursor.execute(update_query, (full_name, college, age, bio, interests_string, user_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Profile updated successfully!"})

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    init_db()
    app.run(debug=True)