from flask import Flask, render_template
from flask_login import LoginManager, current_user

app = Flask(__name__)
app.secret_key = 'test-key'

login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
