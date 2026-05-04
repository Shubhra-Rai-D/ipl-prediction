from flask import Flask, render_template, redirect, session, request, url_for, flash
import pickle
import pandas as pd
import numpy as np
import os
from supabase import create_client, Client
from hashlib import sha256

# ------------------ SUPABASE CONFIG ------------------
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

# ------------------ FLASK APP ------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "1234")

# ------------------ LOAD MODEL SAFELY ------------------
model = None
if os.path.exists('ipl.pkl'):
    with open('ipl.pkl', 'rb') as f:
        model = pickle.load(f)
else:
    print("⚠️ Model file (ipl.pkl) not found!")

# ------------------ PASSWORD HASH ------------------
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# ------------------ PREDICTION FUNCTION ------------------
def predict_score(bat_team='Mumbai Indians', bowl_team='Delhi Daredevils',
                  runs=120, wickets=4, overs=6.2, runs_last_5=33, wickets_last_5=1):

    temp_array = []

    teams = [
        'Chennai Super Kings', 'Delhi Daredevils', 'Kings XI Punjab',
        'Kolkata Knight Riders', 'Mumbai Indians', 'Rajasthan Royals',
        'Royal Challengers Bangalore', 'Sunrisers Hyderabad'
    ]

    for team in teams:
        temp_array.append(1 if bat_team == team else 0)

    for team in teams:
        temp_array.append(1 if bowl_team == team else 0)

    temp_array += [runs, wickets, overs, runs_last_5, wickets_last_5]

    temp_array = np.array([temp_array])

    if model:
        return int(model.predict(temp_array)[0])
    else:
        return "Model not loaded"

# ------------------ ROUTES ------------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')

        existing = supabase.table('users').select("*").eq("email", email).execute()

        if existing.data:
            flash("Email already exists", "error")
            return redirect(url_for("register"))

        hashed_password = hash_password(password)

        supabase.table("users").insert({
            "uname": email.split('@')[0],
            "email": email,
            "password": hashed_password
        }).execute()

        flash("Registration successful", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')

        hashed_password = hash_password(password)

        result = supabase.table('users').select("*") \
            .eq("email", email).eq("password", hashed_password).execute()

        if result.data:
            session['user_id'] = result.data[0]['email']
            session['email'] = email
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if 'user_id' not in session:
        return redirect(url_for("login"))

    if request.method == 'POST':
        bat_team = request.form.get('bat_team')
        bowl_team = request.form.get('bowl_team')
        overs = float(request.form.get('overs'))
        wickets = int(request.form.get('wickets'))
        runs = int(request.form.get('runs'))
        runs_last_5 = int(request.form.get('runs_last_5'))
        wickets_last_5 = int(request.form.get('wickets_last_5'))

        score = predict_score(
            bat_team, bowl_team, runs, wickets,
            overs, runs_last_5, wickets_last_5
        )

        return render_template('predict.html', prediction=score)

    return render_template('predict.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

# ------------------ MAIN ------------------

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)