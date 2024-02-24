from flask_socketio import SocketIO
import json
from database import Database
from resource_fetcher import ResourceFetcher
resource_fetcher = ResourceFetcher()

socketio = SocketIO()
db = Database(socketio)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('get_departments')
def get_departments(message):
    departments_data_binary = resource_fetcher.fetch_resource_file("departement")
    departments_data_string = departments_data_binary.decode('utf-8')
    departments_data_json = json.loads(departments_data_string)
    socketio.emit('departments', departments_data_json)
    
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('fetch_departments_adresses')
def fetch_departments_adresses(message):
    db.fetch_departments_adresses(message)
    socketio.emit('fetching_infos', "done")

@socketio.on('search_adresse')
def search_adresse(message):
    result = db.find_addresses_by_keywords(message)
    socketio.emit('search_adresse_result', result)
