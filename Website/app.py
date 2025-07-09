from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

PIN_CODE = "1234"

@app.route('/')
def home():
    return render_template("MainPage.html")

@app.route('/projects')
def GetProjectPage():
    print('ka;sdlf')
    return render_template("Projects.html")

@app.route('/access', methods=['GET', 'POST'])
def access():
    if request.method == 'POST':
        pin = request.form.get('pin')
        session['has_access'] = True
        session['has_pin'] = (pin == PIN_CODE)
        return redirect(url_for('projects'))
    return render_template('access.html')

@app.route('/projects')
def projects():
    if not session.get('has_access'):
        return redirect(url_for('access'))

    editable = session.get('has_pin', False)
    return render_template('projects.html', editable=editable)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)