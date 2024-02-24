from flask_socketio import SocketIO
from flask_cors import CORS
import json
from database import Database
from resource_fetcher import ResourceFetcher
resource_fetcher = ResourceFetcher()
RADIUS = 100

socketio = SocketIO(cors_allowed_origins="*")
db = Database(socketio)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('get_departments')
def get_departments():
    departments_data_binary = resource_fetcher.fetch_resource_file("departement")
    departments_data_string = departments_data_binary.decode('utf-8')
    departments_data_json = json.loads(departments_data_string)
    socketio.emit('departments', departments_data_json)

@socketio.on('search_point_of_interest')
def search_keywords_poi(message):
    center_lat, center_lon, keywords, radius = deserialize_message(message)
    search_results = db.search_poi_within_radius_with_keywords(center_lat, center_lon, radius, keywords)
    socketio.emit('point_of_interests', serialize_pois(search_results))

def serialize_pois(pois):
    serialized_pois = []
    for poi in pois:
        serialized_pois.append({
            'id': poi[0],
            'name': poi[1],
            'type': poi[2],
            'longitude': poi[3],
            'latitude': poi[4]
    })
    return serialized_pois

def deserialize_message(message):
    return message['latitude'], message['longitude'], message['keywords'], message["radius"]