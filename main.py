from flask import Flask, render_template, request, flash, redirect, url_for, session, g
import requests
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from werkzeug.utils import secure_filename
from datetime import datetime
dirname = os.path.dirname(__file__)

app = Flask(__name__)
app.secret_key = 'mysecretkey'

dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
s3 = boto3.client('s3')
BUCKET_NAME = 'mysocialapp2'
users = dynamodb.Table('users')

@app.before_request
def before_request():
    g.email = None
    g.username = None
    
    if 'user_email' in session:
        user_email = session['user_email']
        g.email = user_email
        
        response = users.query(
        KeyConditionExpression=Key('email').eq(g.email)
        )
        g.username = response['Items'][0]['username']

@app.route('/')
def index():
    return render_template('index.html', is_index = True)

@app.route('/home',methods=['GET','POST'])
def home():
    response = users.get_item(Key={'email': g.email})
    user = response['Item']
    if request.method == 'GET':
        return render_template('home.html', user = user)
    
@app.route('/edit/profile',methods=['GET','POST'])
def edit_profile():
    if request.method == 'GET':
        response = users.get_item(Key={'email': g.email})
        user = response['Item']
        return render_template('edit_profile.html', user = user)
    elif request.method == 'POST':   
        response = users.get_item(Key={'email': g.email})
        user = response['Item']
             
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
                
        users.update_item(
        Key={
            'email': g.email
        },
        UpdateExpression="set username = :u, about = :a, age = :age, loc= :loc, image_path = :i",
        ExpressionAttributeValues={
            ":u" : username,
            ":a" : about,
            ":age" : age,
            ":loc" : location,
            ":i" : image,                  
        }
        )
        return redirect(url_for('edit_profile'))
    
@app.route('/edit/password',methods=['GET','POST'])
def edit_password():
    if request.method == 'GET':
        response = users.get_item(Key={'email': g.email})
        user = response['Item']
        return render_template('edit_password.html', user = user)
    elif request.method == 'POST':   
        response = users.get_item(Key={'email': g.email})
        user = response['Item']
        
        old_pw = request.form.get('edit-old-pw')
        new_pw = request.form.get('edit-new-pw')
    
                
        users.update_item(
        Key={
            'email': g.email
        },
        UpdateExpression="set password = :p",
        ExpressionAttributeValues={
            ":p" : password               
        }
        )
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
        
        response = users.query(
            KeyConditionExpression=Key('email').eq(email_signup)
        )
        
        if response['Items']:
            error = "The email already exists"  

        # OLD DB CODE
        # else:
        #     users.put_item(
        #         Item={
        #             'email': email_signup,
        #             'username': username_signup,
        #             'password' : password_signup,
        #             'date' : date
        #         }
        #     )
        #     return redirect(url_for('login'))

        else:
            payload = {
                "operation": "create",
                "tableName": "users",
                "payload":{
                    "email": "kevy@hotmail.com ",
                    "date" : "2021-11-30",       
                    "password" : "asldfkjasdf",             
                    "username": "asdlfkasjldfkj"
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
        
        response = users.query(
        KeyConditionExpression=Key('email').eq(email_login),
        FilterExpression=Attr('password').eq(password_login)
        )
        if not response['Items']:
            error = "Email or password is invalid"  
        else:
            session['user_email'] = email_login
            return redirect(url_for('home'))
    return render_template('login.html',error = error)

@app.route('/logout')
def logout():
   session.pop('user_email', None)
   return redirect(url_for('login'))
        
if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
 