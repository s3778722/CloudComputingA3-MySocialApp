from flask import Flask, render_template, request, flash, redirect, url_for, session, g
import requests
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.utils import secure_filename
from datetime import datetime
dirname = os.path.dirname(__file__)

application = app = Flask(__name__)
app.secret_key = 'mysecretkey'

s3 = boto3.client('s3')
BUCKET_NAME = 'mysocialapp2'

@app.before_request
def before_request():
    g.email = None
    g.username = None
    
    if 'user_email' in session:
        user_email = session['user_email']
        g.email = user_email

        payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": g.email
            }
        }
        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        responseJson = response.json()
        g.username = responseJson['Item']['username']

@app.route('/')
def index():
    return render_template('index.html', is_index = True)

@app.route('/home',methods=['GET','POST'])
def home():
    payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": g.email
            }
        }
    response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
    responseJson = response.json()

    user = responseJson['Item']

    payload = {
        "operation": "query",
        "tableName": "posts",
        "payload": {
            "index": "GSI-datetime-index",
            "key" : "GSI",
            "eq" : "ok",
            "ascending" : "false"
        }
    }
    response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
    responseJson = response.json()
    posts = responseJson['Items']

    if request.method == 'GET':
        return render_template('home.html', user = user, posts = posts)
    
    elif request.method == 'POST':
        payload = {
            "operation": "create",
            "tableName": "posts",
            "payload": {
                "id": 101,
                "content": request.form.get('post-content'),
                "likes": "0",
                "username": g.username
            }
        }

        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        return redirect(url_for('home'))

@app.route('/post',methods=['GET','POST'])
def post():
    payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": g.email
            }
        }
    response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
    responseJson = response.json()

    user = responseJson['Item']

    idStr = request.args.get('id')
    id = int(idStr)
    payload = {
            "operation": "read",
            "tableName": "posts",
            "payload": {
                "id": id
            }
        }
    response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
    responseJson = response.json()
    post = responseJson['Item']

    payload = {
        "operation": "query",
        "tableName": "comments",
        "payload": {
            "index": "postid-datetime-index",
            "key" : "postid",
            "eq" : id,
            "ascending" : "true"
            }
        }
    response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
    responseJson = response.json()
    comments = responseJson['Items']

    if request.method == 'GET':
        return render_template('post.html', user = user, post = post, comments = comments)
    
#     elif request.method == 'POST':
#         payload = {
#             "operation": "create",
#             "tableName": "posts",
#             "payload": {
#                 "id": 101,
#                 "content": request.form.get('post-content'),
#                 "likes": "0",
#                 "username": g.username
#             }
#         }

#         response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
#         return redirect(url_for('home'))

    
@app.route('/edit/profile',methods=['GET','POST'])
def edit_profile():
    if request.method == 'GET':
        payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": g.email
            }
        }
        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        responseJson = response.json()

        user = responseJson['Item']
        return render_template('edit_profile.html', user = user)
    elif request.method == 'POST':
        payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": g.email
            }
        }
        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        responseJson= response.json()

        user = responseJson['Item']
             
        username = request.form.get('edit-username')
        about = request.form.get('edit-aboutme')
        age = request.form.get('edit-age')
        location = request.form.get('edit-location')
        img = request.files['edit-image']
        
        if img:
            image = 'https://mysocialapp2.s3.us-east-2.amazonaws.com/' + g.email
            filename = secure_filename(img.filename)
            filename = os.path.join(dirname, 'static/img/'+ filename)
            img.save(filename)
            s3.upload_file(
                Bucket = BUCKET_NAME,
                Filename=filename,
                Key = g.email
            )
        else:
            if 'image_path' in user:
                image = user['image_path']
            else:
                image = None

        payload = {
            "operation": "update",
            "tableName": "users",
            "payload": {
                "key": {
                    "email": g.email
                },
                "UpdateExpression": "set username = :u, about = :a, age = :age, loc= :loc, image_path = :i",
                "ExpressionAttributeValues": {
                    ":u": username,
                    ":a": about,
                    ":age": age,
                    ":loc": location,
                    ":i": image
                }
            }
        }
            
        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        return redirect(url_for('edit_profile'))
    
@app.route('/edit/password',methods=['GET','POST'])
def edit_password():
    if request.method == 'GET':
        payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": g.email
            }
        }
        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        responseJson= response.json()

        user = responseJson['Item']
        return render_template('edit_password.html', user = user)
    elif request.method == 'POST':   
        payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": g.email
            }
        }

        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        responseJson= response.json()

        user = responseJson['Item']
        
        old_pw = request.form.get('edit-old-pw')
        new_pw = request.form.get('edit-new-pw')
    
        if old_pw == user['password']:

            payload = {
                "operation": "update",
                "tableName": "users",
                "payload": {
                    "key": {
                        "email": g.email
                    },
                    "UpdateExpression": "set password = :p",
                    "ExpressionAttributeValues": {
                        ":p" : new_pw
                    }
                }
            }
            
            response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
            flash('Password updated successfully')
        else:
            flash('The old password is incorrect')
        return redirect(url_for('edit_password'))

@app.route('/signup',methods=['GET','POST'])
def register():
    date = datetime.now()
    date = date.strftime('%Y-%m-%d')
    
    if 'user_email' in session:
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        error = None
        email_signup = request.form.get('signup-email')
        username_signup = request.form.get('signup-username')
        password_signup = request.form.get('signup-password')
        
        payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": email_signup
            }
        }

        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        responseJson= response.json()
        
        if 'Item' in responseJson:
            error = "The email already exists"  

        else:
            payload = {
                "operation": "create",
                "tableName": "users",
                "payload":{
                    "email": email_signup,
                    "date" : date,       
                    "password" : password_signup,             
                    "username": username_signup
                }
            }
            
            response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
            print(response)
            return redirect(url_for('login'))
        
    return render_template('signup.html',error = error)

@app.route('/login',methods=['GET','POST'])
def login():
    if 'user_email' in session:
        return redirect(url_for('home'))
    
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        error = None
        email_login = request.form.get('login-email')
        password_login = request.form.get('login-password') 

        payload = {
            "operation": "read",
            "tableName": "users",
            "payload": {
                "email": email_login
            }
        }

        response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
        responseJson= response.json()
        
        if 'Item' not in responseJson:
            error = "User does not exist, sign up!" 

        elif responseJson['Item']['password'] != password_login:
            error = "Password is incorrect!" 

        else:
            session['user_email'] = email_login
            return redirect(url_for('home'))
    return render_template('login.html',error = error)

@app.route('/logout')
def logout():
   session.pop('user_email', None)
   return redirect(url_for('login'))

@app.route('/delete/profile-picture')
def deletepp():
    s3.delete_object(Bucket=BUCKET_NAME,Key=g.email)
    payload = {
        "operation": "update",
        "tableName": "users",
        "payload": {
            "key": {
                "email": g.email
            },
            "UpdateExpression" : "set image_path = :i",
            "ExpressionAttributeValues": {
                ":i" : None
            }
        }
    }
            
    response = requests.post('https://7c77wv9c2g.execute-api.us-east-1.amazonaws.com/api/query', json = payload, verify=True)
    return redirect(url_for('home'))
        
if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
 