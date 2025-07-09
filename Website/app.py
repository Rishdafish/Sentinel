import asyncio 
from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

PIN_CODE = "1213461346234623642323462310"

@app.route('/')
def home():
    return render_template("MainPage.html")

@app.route('/access', methods=['GET', 'POST'])
def GetAccessPage():
    if request.method == 'POST':
        pin = request.form.get('pin')
        if pin == PIN_CODE:
            session['role'] = 'admin'
            return redirect(url_for('GetProjectPage'))
        elif 'guest' in request.form:
            session['role'] = 'guest'
            return redirect(url_for('GetProjectPage'))
        else:
            return render_template('Access.html', error="Invalid PIN.")
    if session.get('role') in ['admin', 'guest']:
        return redirect(url_for('GetProjectPage'))

    return render_template('Access.html')

@app.route('/projects')
def GetProjectPage():
    role = session.get('role')
    if role in ['admin', 'guest']:
        if role == 'admin':
            editable = True
        return render_template('Projects.html', editable=editable)
    return redirect(url_for('GetAccessPage'))


if __name__ == '__main__':
    app.run(debug=True)