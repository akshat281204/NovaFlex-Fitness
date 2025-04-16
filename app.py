from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from waitress import serve
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('secret_key')

firebase_credentials = os.getenv('firebase_credentials')

cred_dict = json.loads(firebase_credentials)

cred = credentials.Certificate(cred_dict)
initialize_app(cred)
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
    return render_template('su.html')

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
    username = request.form['li_Username']
    password = request.form['li_password']

    user_ref = db.collection('users').document(username)
    user_doc = user_ref.get()

    if user_doc.exists and check_password_hash(user_doc.to_dict().get('password'), password):
        session['username'] = username
        return redirect('/home')
    else:
        error_message = "Invalid username or password. Please try again."
        return render_template('su.html', error=error_message)

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

# Using Waitress to serve the app in production
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)  # Adjust host and port as needed