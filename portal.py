from flask import Flask, render_template, request, flash, redirect, url_for, session, g
import requests
import boto3

app = Flask(__name__)
app.secret_key = 'mysecretkey'

@app.before_request
def before_request():
    g.id = None
    
    if 'user_admin' in session:
        user_admin = session['user_admin']
        g.username = user_admin

@app.route('/portal', methods=['GET','POST'])
def portal():
    if not 'user_admin' in session:
        return redirect(url_for('index'))

    if request.method == 'GET':
        return render_template('portal.html')
    
    if request.method == 'POST':
        query = request.form.get('query')

        payload = {
            'operation': 'query',
            'query': query
        }
        response = requests.post('https://hfb8rnrjji.execute-api.us-east-1.amazonaws.com/api/athena', json = payload, verify=True)
        responseJson = response.json()
        print(responseJson)

        return render_template('portal.html', json=responseJson)

@app.route('/',methods=['GET','POST'])
def index():
    if 'user_admin' in session:
        return redirect(url_for('portal'))
    
    if request.method == 'GET':
        return render_template('portal_login.html')
    elif request.method == 'POST':
        error = None
        username_login = request.form.get('login-username')
        password_login = request.form.get('login-password') 
        
        if username_login != 'admin':
            error = "Invalid admin user!" 

        elif password_login != 'admin':
            error = "Password is incorrect!" 

        else:
            session['user_admin'] = username_login
            return redirect(url_for('portal'))
    return render_template('portal_login.html',error = error)

@app.route('/logout')
def logout():
   session.pop('user_admin', None)
   return redirect(url_for('index'))
        
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80, debug=True)
 