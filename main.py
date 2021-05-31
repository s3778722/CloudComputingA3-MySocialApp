from flask import Flask, render_template, request, flash, redirect, url_for, session, g
import requests
import boto3
from boto3.dynamodb.conditions import Key, Attr

app = Flask(__name__)
app.secret_key = 'mysecretkey'

dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
s3 = boto3.client('s3')
users = dynamodb.Table('users')

@app.before_request
def before_request():
    g.email = None
    g.username = None
    
    if 'user_email' in session:
        user_email = session['user_email']
        g.email = user_email
        
        response = users_table.query(
        KeyConditionExpression=Key('email').eq(g.email)
        )
        g.username = response['Items'][0]['user_name']

@app.route('/')
def index():
    return render_template('index.html', is_index = True)

@app.route('/signup',methods=['GET','POST'])
def register():
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

        else:
            users.put_item(
                Item={
                    'email': email_signup,
                    'username': username_signup,
                    'password' : password_signup
                }
            )
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
            return redirect(url_for('index'))
    return render_template('login.html',error = error)

@app.route('/logout')
def logout():
   session.pop('user_email', None)
   return redirect(url_for('login'))

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8000, debug=True)
 