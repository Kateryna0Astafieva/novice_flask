from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Blueprint , render_template
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets
from flask_mail import Mail, Message
import logging
import uuid
from flask_login import LoginManager, UserMixin


logging.basicConfig(level=logging.DEBUG)



app = Flask(__name__)

app.secret_key = 'novice_project'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'novice.IT.site@gmail.com'
app.config['MAIL_PASSWORD'] = 'noviceIT2023'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

app.config['SESSION_TYPE'] = 'filesystem'
mail = Mail(app)

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


login_manager = LoginManager(app)
login_manager.login_view = 'login'

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
                    name TEXT, 
        surname TEXT,
       gender TEXT,
        liked_topics TEXT,
        unique_id TEXT NOT NULL,
        remember_token TEXT
             
        )
    ''')

    conn.commit()
    conn.close()

class User(UserMixin):
    def __init__(self, user_id, username, email, password, unique_id):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password
        self.unique_id = unique_id


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)
def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        user = User(user_data['unique_id'], user_data['username'], user_data['email'], user_data['password'], user_data['unique_id'])
        user.remember_token = user_data['remember_token']
        return user
    else:
        return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE unique_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        user = User(user_data['unique_id'], user_data['username'], user_data['email'], user_data['password'], user_data['unique_id'])
        user.remember_token = user_data['remember_token']
        return user
    else:
        return None


auth_bp = Blueprint('auth', __name__)
app.register_blueprint(auth_bp, url_prefix='/auth')

def clear_session():
    session.pop('name', None)
    session.pop('surname', None)
    session.pop('gender', None)


@app.route('/check-auth', methods=['GET'])
def check_authentication():
    isAuthenticated = 'email' in session
    return jsonify({'isAuthenticated': isAuthenticated})




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        unique_id = str(uuid.uuid4()) 
        remember_token = str(uuid.uuid4())

        
        print(f"Original Password: {password}")
        print(f"Hashed Password: {hashed_password}")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, email, password, unique_id, remember_token) VALUES (?, ?, ?, ?, ?)',
               (username, email, hashed_password, unique_id, remember_token))
        
                    

        conn.commit()
        conn.close()
        session['email'] = email
        print(f"User Data: {unique_id}")
        return redirect(url_for('home'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and user['unique_id'] and check_password_hash(user['password'], password):
           session['email'] = email
           session['user_id'] = user['unique_id'] 
           print(f"User Data: {user}")
           print(f"User Data: { user['unique_id'] }")
           return redirect(url_for('home'))
      
        else:
            return 'Invalid email or password. Please try again.'
    
   return render_template('login.html')







@app.route('/save_data', methods=['POST'])
def save_data():
    data = request.json

    user_email = session.get('email')

    if user_email:
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
    UPDATE users
    SET name = ?, surname = ?, gender = ?
    WHERE email = ?
''', (data['name'], data['surname'], data['gender'], session.get('email')))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            print('SQLite error:', e)
        finally:
            conn.close()

        session['name'] = data['name']
        session['surname'] = data['surname']
        session['gender'] = data['gender']

        return jsonify({
            'status': 'success',
            'name': data['name'],
            'surname': data['surname'],
            'gender': data['gender']
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'User not logged in'
        })

@app.route('/load_data')
def load_data():
    user_email = session.get('email')

    if user_email:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (user_email,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return jsonify({
                  'email': user_data['email'], 
                'name': user_data['name'],
                'surname': user_data['surname'],
                'gender': user_data['gender']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            })
    else:
        return jsonify({
            'status': 'error',
            'message': 'User not logged in'
        })



@app.route('/')
def home():
   return render_template('home.html')


@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

def init_password_reset_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        
        if user:

            token = secrets.token_urlsafe(20)
            

            cursor.execute('INSERT INTO password_reset (email, token) VALUES (?, ?)', (email, token))
            conn.commit()
            

            password_reset_link = url_for("reset_password", token=token, _external=True)
            

            msg = Message('Password Reset Request', sender='novice.IT.site@gmail.com', recipients=[email])
            msg.html = render_template('reset_password_email.html', password_reset_link=password_reset_link)
            mail.send(msg)
            
            conn.close()
            return "Instructions to reset your password have been sent to your email."
        else:
            conn.close()
            return "Email address not found. Please try again."
    
    return render_template('forgot_password.html')
            
@app.route('/profile')
def profile():
    if 'email' in session:
        email = session['email']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT liked_topics FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        liked_topics = user['liked_topics'].split(',') if user['liked_topics'] else []
        return render_template('profile.html', liked_topics=liked_topics)
    else:
        return redirect(url_for('login'))



@app.route('/logout')
def logout():

    if 'email' in session:
        session.pop('email', None)
    

    return redirect(url_for('home'))

@app.route('/Topics')
def Topics():
    return render_template('Topics.html')

@app.route('/Topic2')
def Topic2():
    return render_template('Topic2.html')

@app.route('/Topic3')
def Topic3():
    return render_template('Topic3.html')

@app.route('/Topic6')
def Topic6():
    return render_template('Topic6.html')
@app.route('/Topic5')
def Topic5():
    return render_template('Topic5.html')
@app.route('/Topic4')
def Topic4():
    return render_template('Topic4.html')
@app.route('/Topic1')
def Topic1():
    topic = {} 
    return render_template('Topic1.html', topic=topic)
@app.route('/Topic7')
def Topic7():
    return render_template('Topic7.html')
@app.route('/Topic8')
def Topic8():
    return render_template('Topic8.html')
@app.route('/Topic9')
def Topic9():
    return render_template('Topic9.html')
@app.route('/Topic10')
def Topic10():
    return render_template('Topic10.html')
@app.route('/novice')
def novice():
    return render_template('novice.html')
@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/blog')
def blog():
    return render_template('blog.html')



@app.route('/like_topic/<string:topicName>', methods=['POST'])
def like_topic(topicName):
    print(f'Received like request for topic: {topicName}')
    if 'email' in session:
        email = session['email']
        conn = get_db_connection()

        try:
            cursor = conn.cursor()


            cursor.execute('SELECT liked_topics FROM users WHERE email = ?', (email,))
            user_data = cursor.fetchone()

            if not user_data:
                return jsonify({'success': False, 'message': 'User not found.'})

            liked_topics = set(user_data['liked_topics'].split(',') if user_data['liked_topics'] else [])


            if topicName in liked_topics:
                liked_topics.remove(topicName)
                message = f'Topic {topicName} unliked'
            else:
                liked_topics.add(topicName)
                message = f'Topic {topicName} liked'


            cursor.execute('UPDATE users SET liked_topics = ? WHERE email = ?', (','.join(map(str, liked_topics)), email))
            conn.commit()

            print(f"Updated liked topics for {email}: {liked_topics}")

            return jsonify({'success': True, 'message': message, 'liked_topics': list(liked_topics)})

        except Exception as e:
            print(f"Error while updating liked topics: {e}")
            return jsonify({'success': False, 'message': str(e)})

        finally:
            conn.close()
    else:
        return jsonify({'success': False, 'message': 'User not logged in'})

@app.route('/get_liked_topics', methods=['GET'])
def get_liked_topics():
    if 'email' in session:
        try:

            conn = get_db_connection()
            cursor = conn.cursor()

            email = session['email']
            cursor.execute('SELECT liked_topics FROM users WHERE email = ?', (email,))
            user_data = cursor.fetchone()

            if user_data and 'liked_topics' in user_data:
                liked_topics = user_data['liked_topics'].split(',') if user_data['liked_topics'] else []
                print(f"Liked topics for {email}: {liked_topics}")  

                return jsonify({'success': True, 'liked_topics': liked_topics})
            else:

                return jsonify({'success': True, 'liked_topics': []})

        except Exception as e:
            print(f"Error while getting liked topics: {e}")
            return jsonify({'success': False, 'message': repr(e)})

        finally:
            conn.close()
    else:
        return jsonify({'success': False, 'message': 'User not logged in'})

if __name__ == '__main__':
    init_db()
    init_password_reset_db()

    app.run(debug=True, port=5001)