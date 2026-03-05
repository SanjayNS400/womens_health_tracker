from flask import Flask, render_template

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'

@app.route('/')
def home():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
