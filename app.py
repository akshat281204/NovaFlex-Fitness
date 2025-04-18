from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import json
import base64

# Load environment variables
load_dotenv()

firebase_config = {
    "apiKey": os.getenv("google_api"),
    "authDomain": "nova-flex-19015.firebaseapp.com",
    "projectId": "nova-flex-19015",
    "storageBucket": "nova-flex-19015.appspot.com",
    "messagingSenderId": "1052840044112",
    "appId": "1:1052840044112:web:899361e82d2181889d9355",
    "measurementId": "G-J8Z4V1RDZ6"
}

app = Flask(__name__)
app.secret_key = os.getenv('secret_key')

firebase_credentials_b64 = os.environ.get("firebase_credentials")
firebase_credentials_json = base64.b64decode(firebase_credentials_b64).decode("utf-8")
cred_dict = json.loads(firebase_credentials_json)
cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)
db = firestore.client()

# Route for membership page
@app.route('/membership')
def member():
    username = session.get('username')
    if username:
        user_ref = db.collection('users').document(username)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return render_template('mem.html',
                                   home_url=url_for('home'),
                                   user_profile_url=url_for('signup'),
                                   virtual_workouts_url=url_for('virtualworkout'),
                                   gyms_near_you_url=url_for('gyms_near_you'),
                                   gold_membership=user_data.get('gold', 'no'),
                                   platinum_membership=user_data.get('platinum', 'no'))
    return render_template('mem.html',
                           home_url=url_for('home'),
                           user_profile_url=url_for('signup'),
                           virtual_workouts_url=url_for('virtualworkout'),
                           gyms_near_you_url=url_for('gyms_near_you'))

# Route for membership purchase
@app.route('/purchase_membership', methods=['POST'])
def purchase_membership():
    membership_type = request.json.get('membership_type')
    username = session.get('username')
    if username:
        user_ref = db.collection('users').document(username)
        user_ref.update({membership_type: 'yes'})
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'User not logged in'}), 401

# Route for gyms near you
@app.route('/gymsnearyou')
def gyms_near_you():
    return render_template('gny.html',
                           home_url=url_for('home'),
                           user_profile_url=url_for('signup'),
                           virtual_workouts_url=url_for('virtualworkout'),
                           gyms_near_you_url=url_for('gyms_near_you'))

# Route for virtual workout
@app.route('/virtualworkout')
def virtualworkout():
    return render_template('virtworkout.html',
                           home_url=url_for('home'),
                           user_profile_url=url_for('signup'),
                           virtual_workouts_url=url_for('virtualworkout'),
                           gyms_near_you_url=url_for('gyms_near_you'))

# Route for home page (signup/login view)
@app.route('/')
def signup():
    return render_template('su.html', firebase_config=firebase_config)

# Route for user signup
@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form['su_Username']
    phone = request.form['su_Ph_no']
    dob = request.form['su_Date_Of_Birth']
    email = request.form['su_email']
    password = request.form['su_password']

    hashed_password = generate_password_hash(password)

    user_ref = db.collection('users').document(username)
    user_ref.set({
        'username': username,
        'phone': phone,
        'dob': dob,
        'email': email,
        'password': hashed_password,
        'gold': 'no',
        'platinum': 'no'
    })

    return redirect('/home')

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form['li_Username']
        password = request.form['li_password']
        
        user_ref = db.collection('users').document(username)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            stored_password = user_doc.to_dict().get('password')
            
            if check_password_hash(stored_password, password):
                session['username'] = username
                return redirect('/home')
            else:
                error_message = "Incorrect password. Please try again."
                return render_template('su.html', error=error_message)
        else:
            error_message = "Invalid username. Please try again."
            return render_template('su.html', error=error_message)
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}")
        return "Internal Server Error", 500

# Route for home
@app.route('/home')
def home():
    return render_template('home.html',
                           home_url=url_for('home'),
                           user_profile_url=url_for('signup'),
                           virtual_workouts_url=url_for('virtualworkout'),
                           gyms_near_you_url=url_for('gyms_near_you'),
                           membership_url=url_for('member'))

# Profile route
@app.route('/profile')
def profile():
    username = session.get('username')
    if not username:
        return redirect(url_for('signup'))

    user_doc = db.collection('users').document(username).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        return render_template('profile.html', user_data=user_data)
    else:
        return "User not found", 404

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('signup'))
