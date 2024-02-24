from flask import Flask
from socket_handlers import socketio

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key' 

socketio.init_app(app)
 
if __name__ == '__main__':
    socketio.run(app, debug=True)
