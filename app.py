from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import json
import base64
import requests
import uuid
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('secret_key')
CORS(app)

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
    
@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.json
    membership_type = data.get('membership_type')
    username = session.get('username')

    if not username:
        return jsonify({'error': 'Not logged in'}), 401

    order_id = str(uuid.uuid4())
    app_id = os.getenv("cf_id")
    secret_key = os.getenv("cf_secret_key")
    environment = os.getenv("cf_env")

    url = "https://sandbox.cashfree.com/pg/orders" if environment == 'test' else "https://api.cashfree.com/pg/orders"

    headers = {
        "accept": "application/json",
        "x-api-version": "2022-09-01",
        "content-type": "application/json",
        "x-client-id": app_id,
        "x-client-secret": secret_key
    }

    user_doc = db.collection('users').document(username).get().to_dict()
    payload = {
    "order_id": order_id,
    "order_amount": 299 if membership_type == "gold" else 599,
    "order_currency": "INR",
    "customer_details": {
        "customer_id": username,
        "customer_email": user_doc.get("email"),
        "customer_phone": user_doc.get("phone")
    },
    "order_meta": {
        "return_url": f"https://nova-flex-fitness.vercel.app/payment_success?order_id={order_id}&membership_type={membership_type}&username={username}",
        "notify_url": "https://nova-flex-fitness.vercel.app/verify_payment"
    }
    }

    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()

    print("Cashfree response:", json.dumps(response_data, indent=2))

    if 'payments' in response_data and 'url' in response_data['payments']:
        return jsonify({'payment_link': response_data['payments']['url']}), 200
    else:
        return jsonify({
            'error': 'Payment link not received',
            'cashfree_response': response_data
        }), 400

@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    try:
        data = request.get_json()
        print("Cashfree notify payload:", data)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print("Error in verify_payment:", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/payment_success')
def payment_success():
    username = session.get('username')
    membership_type = request.args.get('membership_type')

    if username and membership_type in ['gold', 'platinum']:
        user_ref = db.collection('users').document(username)
        user_ref.update({membership_type: 'yes'})
        return redirect('/home')
    return "Payment failed or user not logged in", 400


# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('signup'))
