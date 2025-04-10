from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = 'nOvAfLeX24'  #Secret key

# MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="akshat@281204",
    database="novaflex"
)

# Route for membership page
@app.route('/membership')
def member():
    cursor = db.cursor()
    username = session.get('username')
    if username:
        cursor.execute("SELECT gold, platinum FROM users WHERE username = %s", (username,))
        user_membership = cursor.fetchone()
        gold_membership = user_membership[0]
        platinum_membership = user_membership[1]
        return render_template('mem.html', home_url=url_for('home'),
                                         user_profile_url=url_for('signup'),
                                         virtual_workouts_url=url_for('virtualworkout'),
                                         gyms_near_you_url=url_for('gyms_near_you'),
                                         gold_membership=gold_membership,
                                         platinum_membership=platinum_membership)
    else:
        return render_template('mem.html', home_url=url_for('home'),
                                         user_profile_url=url_for('signup'),
                                         virtual_workouts_url=url_for('virtualworkout'),
                                         gyms_near_you_url=url_for('gyms_near_you'))


# Route for membership purchase
@app.route('/purchase_membership', methods=['POST'])
def purchase_membership():
    if request.method == 'POST':
        membership_type = request.json.get('membership_type')
        username = session.get('username')  # Get username from session
        if username:
            cursor = db.cursor()
            cursor.execute("UPDATE users SET {} = 'yes' WHERE username = %s".format(membership_type), (username,))
            db.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'User not logged in'}), 401

#route for gyms near you
@app.route('/gymsnearyou')
def gyms_near_you():
    return render_template('gny.html',   home_url=url_for('home'), 
                                         user_profile_url=url_for('signup'),
                                         virtual_workouts_url=url_for('virtualworkout'), 
                                         gyms_near_you_url=url_for('gyms_near_you'))


#route for virtualworkout
@app.route('/virtualworkout')
def virtualworkout():  
    return render_template('virtworkout.html',  home_url=url_for('home'), 
                                         user_profile_url=url_for('signup'),
                                         virtual_workouts_url=url_for('virtualworkout'), 
                                         gyms_near_you_url=url_for('gyms_near_you')) 

#route for home page
@app.route('/')
def signup():
    return render_template('su.html')

#route for user sign up
@app.route('/signup', methods=['POST'])
def signup_post():
    if request.method == 'POST':
        username = request.form['su_Username']
        phone = request.form['su_Ph_no']
        dob = request.form['su_Date_Of_Birth']
        email = request.form['su_email']
        password = request.form['su_password']
        
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, phone, dob, email, password) VALUES (%s, %s, %s, %s, %s)",
                       (username, phone, dob, email, password))
        db.commit()
        return redirect('/home')

#route for user login
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['li_Username']
        password = request.form['li_password']
        
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        if user:
            session['username'] = username
            return redirect('/home')
        else:
            error_message = "Invalid username or password. Please try again."
            return render_template('su.html', error=error_message)

#route for home.html
@app.route('/home')
def home():
    return render_template('home.html', home_url=url_for('home'), 
                                         user_profile_url=url_for('signup'),
                                         virtual_workouts_url=url_for('virtualworkout'), 
                                         gyms_near_you_url=url_for('gyms_near_you'),
                                         membership_url = url_for('member'))

if __name__ == '__main__':
    app.run(debug=True)