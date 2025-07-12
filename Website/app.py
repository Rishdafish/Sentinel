from urllib.parse import urlparse
from openai import OpenAI
import uuid 
import datetime
from typing import List
from flask_cors import cross_origin
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

app = Flask(__name__)
app.secret_key = 'oj;kwfoaenv;kjjak;sdjk;ltj;lk23j4;lk23jl4kj1lkfdjl;k1j3kt89c0vasdfuio01'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/loginPage"
login_manager.session_protection = "basic"
TOKEN = os.environ.get("WEBSITE_TOKEN_VALUE")

def llm_call(prompt: str) -> str:
    client = OpenAI(api_key="sk-9847c361208c4301a20d5f5225d41516", base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=False
    )
    return(response.choices[0].message.content)


def extract_domain(url: str) -> str:
    """
    Given any URL, return its hostname (e.g. 'huggingface.co'),
    stripped of port numbers or credentials.
    """
    parsed = urlparse(url)
    # parsed.netloc might be "user:pass@host:port"
    host = parsed.hostname or ""
    return host.lower()


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



@app.route('/api/addBlogPost', methods=['POST'])
def addBlogPost():
    Title = request.form.get("Title","").strip()
    content = request.form.get("content","").strip()
    dateAndTime = request.form.get("date","").strip()
    if not Title or not content or not dateAndTime:
        return jsonify({"error": "DateAndTime and content and Title are required"}), 400
    blog_id = str(uuid.uuid4())
    blog_data = {
        "id": blog_id,
        "Title": Title,
        "content": content,
        "dateAndTime": dateAndTime

    }
    upload_json(bucket_name="data_for_website", destination_blob_name=f"BlogPosts/{blog_id}.json", data=blog_data)
    return jsonify({"message": "Blog Post added successfully", "id": blog_id})

@app.route('/api/getBlogPosts', methods=['GET'])
def getBlogPosts():
    BlogPosts = getAllDir('BlogPosts/')
    return jsonify(BlogPosts)

@app.route('/api/deleteBlogPost', methods=['POST'])
def deleteBlogPosts():
    blog_id = request.form.get("id", "").strip()
    if not blog_id:
        return jsonify({"error": "Blog ID is required"}), 400
    deleteBlob(bucket_name="data_for_website", blob_name=f"BlogPosts/{blog_id}.json")
    return jsonify({"message": "Blog Post deleted successfully"})

@app.route('/api/changeBlogPosts', methods=['POST'])
def changeBlogPost():
    blog_id = request.form.get("id", "").strip()
    Title = request.form.get("Title", "").strip()
    content = request.form.get("content", "").strip()
    dateAndTime = request.form.get("date", "").strip()

    if not blog_id:
        return jsonify({"error": "Blog ID is required"}), 400

    blog_data = {
        "id": blog_id,
        "Title": Title,
        "content": content,
        "dateAndTime": dateAndTime
    }
    
    upload_json(bucket_name="data_for_website", destination_blob_name=f"BlogPosts/{blog_id}.json", data=blog_data)
    
    return jsonify({"message": "Blog Post updated successfully"})



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


@app.route('/api/ChromeExt/checkWebsite', methods=['POST'])
@cross_origin()
def checkWebsite():
    print('recieved request')
    website = request.form.get("website", "").strip()
    if not website:
        return jsonify({"error": "Website URL is required"}), 400
    allowedWebsites = ['console.cloud.google.com', 'stackoverflow.com', 'leetcode.com','https://ocw.mit.edu','khanacademy.org','https://www.nature.com','https://www.science.org','http://127.0.0.1:5000']
    prompt = f"""You are a URL classifier that enforces my personal “focus” policy.  Given one URL (or domain) as input, return **only** the word `true` if it’s allowed, or `false` if it should be blocked.  No other words, punctuation, or formatting.
        Rules:
        1. **Allow** (return `true`) only when the URL points to:
        - Official documentation (e.g. cloud provider docs, API references).
        -http://127.0.0.1:5000 anything that is locally hosted
        - University course sites (e.g. MIT OpenCourseWare, Berkeley OCW).
        - Research Paper Sites (e.g. arXiv, ResearchGate).
        - Individual GitHub/GitLab/etc. repositories **but not user profiles**.
        2. **Block** (return `false`) when the URL is about:
        - Any person’s profile, bio, or general “about” page (Elon Musk, Yann LeCun, Mark Zuckerberg, Paul Graham, etc.).
        - Any company’s homepage, stock page, or general information (Google, Facebook, Amazon, etc.).
        - News, biographies, or Wikipedia-style information pages about people.
        - Company homepages or stock/financial pages (Palantir, Tesla, Y Combinator, etc.).
        - Entertainment or general-interest sites (movie pages, actor/singer fan pages, Wikipedia, IMDb, music sites).
        - Any general-question or “information-gathering” page not strictly documentation or course material.
        - Any page that is not strictly documentation, course material, or a specific repository, or Scientific papers.
        3. If the URL fits multiple rules, **blocking takes priority**.
        4. Return **only** `true` or `false`.

        **Example inputs → outputs**  
        - `https://cloud.google.com/functions/docs` → `true`  
        - `https://github.com/rishabhiry/my-project` → `true`  
        - `https://github.com/rishabhiry` → `false`  
        - `https://en.wikipedia.org/wiki/Elon_Musk` → `false`  
        - `https://www.imdb.com/title/tt0137523/` → `false`

        **Now classify:**
        {website}"""
    if extract_domain(website) in allowedWebsites:
        print("Website is from list")
        return jsonify({"response": "true"})
    response = llm_call(prompt) 
    if not response:
        return jsonify({"error": "No response from LLM"}), 500
    if response.lower() == "false":
        pass 
    #return jsonify({"response": response})
    print("Response from LLM: ", response)

    return response


if __name__ == "__main__":
    app.run(debug=True)

