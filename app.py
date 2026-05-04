from flask import Flask,render_template,redirect,session,request,url_for,flash

import pickle
import pandas as pd
import numpy as np
from supabase import create_client, Client
from hashlib import sha256

# Supabase configuration
url="https://uckwxyurxibvtuilhtzh.supabase.co"
key="sb_publishable_vArf8jB7nxca5H8IfDM4fw_zghTizSo"
supabase: Client = create_client(url, key)

#create a object for the class flask
app=Flask(__name__)
app.secret_key='1234'

#laoding the model
with open('ipl.pkl','rb') as f:
    model=pickle.load(f)

def hash_password(password):
    return sha256(password.encode()).hexdigest()

#prediction logic
def predict_score(bat_team='Mumbai Indians',bowl_team='Delhi Daredevils',runs=120,wickets=4,overs=6.2,runs_last_5=33,wickets_last_5=1):
    temp_array=list()
    if bat_team == 'Chennai Super Kings':
        temp_array=temp_array+[1,0,0,0,0,0,0,0]
    elif bat_team == 'Delhi Daredevils':
        temp_array=temp_array+[0,1,0,0,0,0,0,0]
    elif bat_team == 'Kings XI Punjab':
        temp_array=temp_array+[0,0,1,0,0,0,0,0]
    elif bat_team == 'Kolkata Knight Riders':
        temp_array=temp_array+[0,0,0,1,0,0,0,0]
    elif bat_team == 'Mumbai Indians':
        temp_array=temp_array+[0,0,0,0,1,0,0,0]
    elif bat_team == 'Rajasthan Royals':
        temp_array=temp_array+[0,0,0,0,0,1,0,0]
    elif bat_team == 'Royal Challengers Bangalore':
        temp_array=temp_array+[0,0,0,0,0,0,1,0]
    elif bat_team == 'Sunrisers Hyderabad':
        temp_array=temp_array+[0,0,0,0,0,0,0,1]
        
    if bowl_team == 'Chennai Super Kings':
        temp_array=temp_array+[1,0,0,0,0,0,0,0]
    elif bowl_team == 'Delhi Daredevils':
        temp_array=temp_array+[0,1,0,0,0,0,0,0]
    elif bowl_team == 'Kings XI Punjab':
        temp_array=temp_array+[0,0,1,0,0,0,0,0]
    elif bowl_team == 'Kolkata Knight Riders':
        temp_array=temp_array+[0,0,0,1,0,0,0,0]
    elif bowl_team == 'Mumbai Indians':
        temp_array=temp_array+[0,0,0,0,1,0,0,0]
    elif bowl_team == 'Rajasthan Royals':
        temp_array=temp_array+[0,0,0,0,0,1,0,0]
    elif bowl_team == 'Royal Challengers Bangalore':
        temp_array=temp_array+[0,0,0,0,0,0,1,0]
    elif bowl_team == 'Sunrisers Hyderabad':
        temp_array=temp_array+[0,0,0,0,0,0,0,1]
    
    temp_array=temp_array+[runs,wickets,overs,runs_last_5,wickets_last_5]

    # converting to numpy array
    temp_array=np.array([temp_array])

    # prediction
    return int(model.predict(temp_array)[0])   

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    return render_template('index.html') 

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        # Form uses 'username' for email field
        email=request.form.get('username')
        password=request.form.get('password')
        
        # Supabase v2.x API - no .execute() needed
        existing = supabase.table('users').select("*").eq("email", email).execute()

        if existing.data:
            flash("Email already exists","error")
            return redirect(url_for("register"))
        
        hashed_password=hash_password(password)
        
        #inserting user into table - Supabase v2.x API
        supabase.table("users").insert({
            "uname":email.split('@')[0],  # Use part before @ as username
            "email":email,
            "password":hashed_password
        }).execute()
        
        flash("Registration successful","success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        
        # Hash the password and check in database
        hashed_password = hash_password(password)
        
        # Supabase v2.x API - no .execute() needed for select
        result = supabase.table('users').select("*").eq("email", email).eq("password", hashed_password).execute()
        
        if result.data and len(result.data) > 0:
            # Set session - use 'email' as user identifier since 'id' may not be available
            session['user_id'] = result.data[0]['email']
            session['email'] = email
            flash("Login successful!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password", "error")
            return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route('/predict', methods=['POST','GET'])
def predict():
    # Require login to access prediction
    if 'user_id' not in session:
        return redirect(url_for("login"))
    
    if request.method == 'POST':
        bat_team=request.form.get('bat_team')
        bowl_team=request.form.get('bowl_team')
        overs=float(request.form.get('overs'))
        wickets=int(request.form.get('wickets'))
        runs=int(request.form.get('runs'))
        runs_last_5=int(request.form.get('runs_last_5'))
        wickets_last_5=int(request.form.get('wickets_last_5'))
        score=predict_score(bat_team=bat_team,bowl_team=bowl_team,runs=runs,wickets=wickets,overs=overs,runs_last_5=runs_last_5,wickets_last_5=wickets_last_5)
        return render_template('predict.html',prediction=score)


    return render_template('predict.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

#create  main function
if __name__=='__main__':
    app.run(debug=True,port=3003,host='0.0.0.0')

