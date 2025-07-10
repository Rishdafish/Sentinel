import asyncio 
import json
from flask import Flask, render_template, request, session, redirect, url_for
from google.cloud import storage
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def searchforEmail(userEmail : str):
    client = storage.Client()
    bucket = client.bucket('data_for_website')
    key = f"users/{userEmail.lower().strip()}.json"
    blob = bucket.blob(key)
    if not blob.exists(): 
        print('User Email is not Found')
        return "Email Does not Exist"
    else: 
        return blob

def verifyCreds():
    pass

def register():
    pass

@app.route('/')
def home():
    return render_template("MainPage.html")

@app.route('/register', methods=['POST', 'GET'])
def registerUser():
    pass

@app.route('/registerPageTypeShit')
def registerPage():
    return render_template('Access.html')


if __name__ == "__main__":
    app.run(debug=True)