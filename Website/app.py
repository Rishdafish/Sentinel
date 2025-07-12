from openai import OpenAI
import uuid 
import datetime
from typing import List
import os
from werkzeug.security import check_password_hash, generate_password_hash
import asyncio 
import json
from flask import Flask, render_template, request, session, redirect, url_for, flash, current_app, jsonify, request, abort
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import flask_login
from google.cloud import storage
from datetime import timedelta
import re
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = "deepseek-ai/deepseek-coder-6.7b-base"
local_dir = "./models/deepseek/"

# Download to local directory
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=local_dir)
model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir=local_dir)


app = Flask(__name__)
app.secret_key = 'oj;kwfoaenv;kjjak;sdjk;ltj;lk23j4;lk23jl4kj1lkfdjl;k1j3kt89c0vasdfuio01'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/loginPage"
login_manager.session_protection = "basic"
TOKEN = os.environ.get("WEBSITE_TOKEN_VALUE")
client = storage.Client()
print(client.project)
bucket = client.bucket('data_for_website')


'''



def llm_call(prompt: str) -> str:
    client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
        ],
        stream=False
    )
    return(response.choices[0].message.content)
 '''   




def deleteBlob(bucket_name: str, blob_name: str):
    """
    Deletes a blob from the specified bucket.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if blob.exists():
        blob.delete()
        print(f"Deleted gs://{bucket_name}/{blob_name}")
    else:
        print(f"Blob gs://{bucket_name}/{blob_name} does not exist.")

def upload_file(bucket_name: str, destination_blob_name: str, source_file_path: str):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_path)  # infers content_type
    print(f"Uploaded file to gs://{bucket_name}/{destination_blob_name}")

def upload_json(bucket_name: str, destination_blob_name: str, data: dict):
    """
    Serializes a dict to JSON and uploads it.
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(
        json.dumps(data),
        content_type='application/json'
    )
    print(f"Uploaded JSON to gs://{bucket_name}/{destination_blob_name}")


def getAllDir(folder: str) -> List[dict]:
    client = storage.Client()
    bucket = client.bucket('data_for_website')
    blobs = bucket.list_blobs(prefix=folder)
    items = []

    for blob in blobs:
        # skip directory markers
        if blob.name.endswith('/'):
            continue
        raw = blob.download_as_text()
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # not valid JSON → skip
            continue
        items.append(data)
    return items

class User(UserMixin):
    def __init__(self, emailID: str, password: str, token = None):
         self.id = emailID.lower().strip()
         self.Password = password
         if token == TOKEN:
            self.role = "admin"
         else: 
            self.role = 'standard'

    @classmethod
    def get(cls, email: str):
        client = storage.Client()
        bucket = client.bucket("data_for_website")
        blob   = bucket.blob(f"users/{email.lower().strip()}.json")

        # Return None if there’s no such user
        if not blob.exists():
            return None

        raw  = blob.download_as_text()
        data = json.loads(raw)
        return cls(
            emailID = data["email"],
            password= data["PasswordHash"],
            token   = data.get("token")
    )

def verifyCreds(userEmail : str, password: str):
    client = storage.Client()
    bucket = client.bucket('data_for_website')
    key = f"users/{userEmail.lower().strip()}.json"
    blob = bucket.blob(key)
    if not blob.exists(): 
        return "Email Does not Exist"
    raw = blob.download_as_text()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return "Corrupted Data in Json"
    stored_email = data["email"]
    stored_hash  = data["PasswordHash"]
    if stored_email == userEmail and check_password_hash(stored_hash, password):
        return "True"
    return "Incorrect Password"

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/logout")
def logout():
    logout_user()
    print("User Logged Out")
    return redirect('MainPage.html')

@app.route('/loginPage', methods=["POST", "GET"])
def login():
    if request.method == ('GET'):
        return render_template('Access.html')
    elif request.method == "POST":
        formEmail = request.form.get('email')
        formPassword = request.form.get('password')
        if verifyCreds(userEmail = formEmail, password = formPassword) != "Email Does not Exist":
            user = User(emailID = formEmail, password = formPassword)
            flask_login.login_user(user, remember=True, duration=(timedelta(days=365)))
            print("Login Successful")
            return render_template('MainPage.html')
        
@app.route('/registerPage', methods=['POST','GET'])
def register():
    if request.method == ("POST"):
        formEmail = request.form.get('email')
        formPassword = request.form.get('password')
        if request.form.get('token') == "":
            formToken = None
        else: 
            formToken = request.form.get('token') 
        print('IS the storage working ')
        client = storage.Client()
        print('possbily')
        tempJson = {
            "email": formEmail,
            "PasswordHash": generate_password_hash(formPassword),
            "token" : formToken
        }
        json_text = json.dumps(tempJson)
        try: 
            upload_json(data=tempJson, bucket_name='data_for_website', destination_blob_name=f'users/{formEmail.lower().strip()}.json')
            flash("Account created! You can now log in.", "success")
            user = User(emailID=formEmail, password=formPassword, token=formToken)
            flask_login.login_user(user, remember=True, duration=(timedelta(days=365)))
            return redirect(url_for('home'))
        except Exception as e: 
            current_app.logger.error(f"Failed to upload user blob: {e}")
            print('Exception Error ')
            flash("Oops, something went wrong when creating your account. Please try again.", "danger")
    else: 
        return render_template('Access.html')
    
@app.route('/getAllProjects', methods = ['GET'])
def getAllProjects():
    return jsonify(getAllDir('Projects/'))

@app.route('/api/changeProject', methods=['POST'])
@login_required
def change_project():
    project_id = request.form.get("id", "").strip()
    title       = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    tags        = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
    githubURL   = request.form.get("github", "").strip()
    progression = request.form.get("progression", "").strip()
    endDate = request.form.get("endDate", "").strip()

    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    project_data = {
        "id": project_id,
        "title": title,
        "description": description,
        "tags": tags,
        "github": githubURL,
        "progression": progression,
        'endDate': endDate
    }
    
    upload_json(bucket_name="data_for_website", destination_blob_name=f"Projects/{project_id}.json", data=project_data)
    
    return jsonify({"message": "Project updated successfully"})

@app.route("/uploadProject", methods=["POST"])
@login_required
def upload_project():
    title       = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    tags        = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
    githubURL   = request.form.get("github", "").strip()
    progression = request.form.get("progression", "").strip()
    endDate    = request.form.get("endDate", "").strip()

    project_id = str(uuid.uuid4())

    project_data = {
        "id": project_id,
        "title": title,
        "description": description,
        "tags": tags,
        "github": githubURL,
        "progression": progression,
        'endDate': endDate
    }
    upload_json(bucket_name="data_for_website", destination_blob_name=f"Projects/{project_id}.json", data=project_data)
    return jsonify({"message": "Project uploaded successfully", "id": project_id})

@app.route('/api/deleteProject', methods=['POST'])
@login_required
def delete_project():
    project_id = request.form.get("id", "").strip()
    
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    # Delete the project blob
    deleteBlob(bucket_name="data_for_website", blob_name=f"Projects/{project_id}.json")
    
    return jsonify({"message": "Project deleted successfully"})

@app.route('/api/addQuote', methods=['POST'])
def addQuote():
    quote = request.form.get("quote","").strip()
    author = request.form.get("author","").strip()
    if not quote or not author:
        return jsonify({"error": "Quote and author are required"}), 400
    quote_id = str(uuid.uuid4())
    quote_data = {
        "id": quote_id,
        "quote": quote,
        "author": author
    }
    upload_json(bucket_name="data_for_website", destination_blob_name=f"Quotes/{quote_id}.json", data=quote_data)
    return jsonify({"message": "Quote added successfully", "id": quote_id})

@app.route('/api/getQuotes', methods=['GET'])
def getQuotes():
    quotes = getAllDir('Quotes/')
    return jsonify(quotes)

@app.route('/api/deleteQuote', methods=['POST'])
def deleteQuote():
    quote_id = request.form.get("id", "").strip()
    if not quote_id:
        return jsonify({"error": "Quote ID is required"}), 400
    deleteBlob(bucket_name="data_for_website", blob_name=f"Quotes/{quote_id}.json")
    return jsonify({"message": "Quote deleted successfully"})

@app.route('/api/changeQuote', methods=['POST'])
def changeQuote():
    quote_id = request.form.get("id", "").strip()
    quote = request.form.get("quote", "").strip()
    author = request.form.get("author", "").strip()

    if not quote_id:
        return jsonify({"error": "Quote ID is required"}), 400

    quote_data = {
        "id": quote_id,
        "quote": quote,
        "author": author
    }
    
    upload_json(bucket_name="data_for_website", destination_blob_name=f"Quotes/{quote_id}.json", data=quote_data)
    
    return jsonify({"message": "Quote updated successfully"})


@app.route('/')
def home():
    return render_template("MainPage.html")

@app.route('/Projects')
@login_required
def GetProjectPage():
    return render_template('Projects.html')

@app.route('/Books')
@login_required
def GetBooksPage():
    return render_template('Books.html')

@app.route('/Hours')
@login_required
def GetHoursPage():
    return render_template('Hours.html')

@app.route('/Blog')
@login_required
def GetBlogPage():
    return render_template('Blog.html')

@app.route('/Quotes')
@login_required
def GetQuotesPage():
    return render_template('Quotes.html')

@app.route('/api/chromeExtension/request', methods=['GET'])
def chrome_extension_request():
    pass 


if __name__ == "__main__":
    app.run(debug=True)