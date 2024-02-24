from datetime import datetime
from flask_socketio import SocketIO
import json
import re
import csv
import pyodbc 
from resource_fetcher import ResourceFetcher
from position_converter import PositionConverter
import os


IGNORED_WORDS = ["le", "la", "les", "des", "de", "du", "un", "une", "au", "aux", "ce", "cette", "ces", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "notre", "nos", "votre", "vos", "leur", "leurs"]

class Database:
    def __init__(self, socket: SocketIO):
        self.conn = None
        self.cursor = None
        self.socket = socket
        self.resource_fetcher = ResourceFetcher()
        self.postion_converter = PositionConverter()
        self.resources = self.load_config()
        self.open_connection()
        self.create_tables()
        self.fetch_resources()
        self.close()

    def load_config(self):
        with open( "config.json", 'r') as f:
            config_data = json.load(f)
            return config_data.get('resources', [])

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def open_connection(self):
        try:
            self.conn = pyodbc.connect('DRIVER={SQL Server};SERVER=LAPTOP-GJG875RR\SQLEXPRESS;DATABASE=geoki;Trusted_Connection=yes;')
            self.cursor = self.conn.cursor()
            print("Connection established successfully!")
        except pyodbc.Error as e:
            print(f"Error establishing connection: {e}")

    def create_tables(self):
        print("Creating tables...")
        self.create_point_of_interest_table()
        self.create_dictionary_table()
        self.create_dictionary_references_table()
        self.commit()

    def create_point_of_interest_table(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'point_of_interest')
            BEGIN
                CREATE TABLE point_of_interest (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(255) NOT NULL,
                    type NVARCHAR(255) NOT NULL,
                    longitude FLOAT,
                    latitude FLOAT,
                    x float,
                    y float
                );
            END
        ''')

    def create_dictionary_table(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dictionnary')
            BEGIN
                CREATE TABLE dictionnary (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    word NVARCHAR(255) NOT NULL
                );
            END
        ''')

    def create_dictionary_references_table(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'dictionnary_reference')
            BEGIN
                CREATE TABLE dictionnary_reference (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    dictionary_id INT NOT NULL,
                    reference_id INT NOT NULL,
                    FOREIGN KEY (dictionary_id) REFERENCES Dictionnary (id)
                );
            END
        ''')

    def create_indexes(self):
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON dictionnary (word)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON point_of_interest (type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_dic ON dictionnary_reference (dictionary_id)")

    def fetch_resources(self):
        for resource in self.resources:
            if(resource['done'] == False and resource["resource_type"] == "poi"):
                #print(resource)
                self.fetch_one_resource(resource)

    def fetch_one_resource(self, resource):
        name = resource['resource_name']
        file_path = f"downloads/{name}.csv"

        if not os.path.exists(file_path):
            with open(file_path, "wb") as f:
                f.write(self.resource_fetcher.fetch_resource_file(name))

        total_lines = sum(1 for line in open(file_path, "r", encoding="utf-8"))

        print(f"Total lignes: {total_lines}") 

        self.open_connection()
        self.parse_csv(resource, total_lines)
        self.close()

    def parse_csv(self,resource,total_lines):
        name= resource['resource_name']
        with open(f"downloads/{name}.csv", "r", encoding="utf-8") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';')
            next(csvreader)
            current_line = 0
            for row in csvreader:
                current_line += 1
                adresse_id, name = self.insert_point_of_intereset(row, resource)
                if adresse_id is None:
                    continue
                print(f"{current_line}/{total_lines}")
                self.insert_in_dictionary(adresse_id, name)
                self.commit()

    def insert_point_of_intereset(self, row, resource):
        schema = resource['schema']
        name = row[schema['name_col']]
        if  schema['type_col'] == None:
            type = resource["resource_name"]
        else:
            type =  row[schema['type_col']]
        longitude = row[schema['longitude_col']]
        parts = longitude.split(',')
        if len(parts) > 1:
            latitude = parts[0]
            longitude = parts[1]
        else:
            latitude =  row[schema['latitude_col']]

        if not all([name, type, longitude, latitude]):
            print("Certaines informations nécessaires sont manquantes dans la ligne CSV.")
            return None, None
        
        ## print( "%s, %s, %s, %s" % (name, type, longitude, latitude))
        
        x, y = self.postion_converter.convert_lat_lon_to_xy(longitude, latitude)
        
        self.cursor.execute('''INSERT INTO point_of_interest (name, type, longitude, latitude, x, y) output inserted.ID 
                    VALUES (?, ?, ?, ?, ?, ?)''', (name, type, longitude, latitude, x, y))
        last_row_id = self.cursor.fetchone()[0]

        return last_row_id, name
         
    def split_name(self, street_name):
        return re.split(r'[\s_\'°-]', street_name)
        
    def filter_words(self, words):
        filtered_words = []
        type= None
        for word in words:
            word = word.lower()
            if len(word) >= 2 and not word.isdigit() and word not in IGNORED_WORDS:
                if word in self.get_distinct_types() and type is None:
                    type = word
                else:
                    filtered_words.append(word)
        return filtered_words, type
    
    def get_distinct_types(self):
        distinct_types = set()
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT type FROM point_of_interest") 
        rows = cursor.fetchall()
        for row in rows:
            distinct_types.add(row.type)
        return distinct_types

    def insert_in_dictionary(self, reference_id, name):
        filtered_words = self.filter_words(self.split_name( name))
        for word in filtered_words:
            self.cursor.execute("SELECT id FROM dictionnary WHERE word = ?", (word,))
            existing_word = self.cursor.fetchone()
            if existing_word:
                self.cursor.execute('''
                    INSERT INTO dictionnary_reference (dictionary_id, reference_id)
                    VALUES (?, ?)''',
                    (existing_word[0], reference_id ))
            else:
                self.cursor.execute('''
                    INSERT INTO dictionnary (word)
                    output inserted.ID 
                    VALUES (?)''',
                    (word,))
                dictionary_id = self.cursor.fetchone()[0]
                
                self.cursor.execute('''
                    INSERT INTO dictionnary_reference (dictionary_id, reference_id)
                    VALUES (?, ? )''',
                    (dictionary_id, reference_id ))
                
    def search_poi_within_radius_with_keywords(self, center_lat=None, center_lon=None, radius=100, keywords=None):
        self.open_connection()
        query = """
            SELECT poi.id, poi.name, poi.type, poi.longitude, poi.latitude
            FROM point_of_interest poi
            JOIN dictionnary_reference dr ON poi.id = dr.reference_id
            JOIN dictionnary d ON dr.dictionary_id = d.id
            WHERE 1=1
        """
        params = []

        if center_lat is not None and center_lon is not None and radius is not None:
            query += """
                AND 6371000 * 2 * ASIN(SQRT(
                    POWER(SIN((RADIANS(poi.latitude) - RADIANS(?)) / 2), 2) +
                    COS(RADIANS(?)) * COS(RADIANS(poi.latitude)) *
                    POWER(SIN((RADIANS(poi.longitude) - RADIANS(?)) / 2), 2)
                )) <= ?
            """
            params.extend([center_lat, center_lat, center_lon, radius])

        if keywords:
            keywords, type = self.filter_words(self.split_name(keywords))
            if keywords:
                keywords = [f"%{word}%" for word in keywords]
                query += " AND (d.word LIKE ? "
                for i in range(1, len(keywords)):
                    query += "OR d.word LIKE ? "
                query += ")"
                params.extend(keywords)  # Ajouter les paramètres correspondants ici

        if type:
            query += " AND poi.type = ?"
            params.append(type)

        self.cursor.execute(query, params)
        responses = self.cursor.fetchall()
        self.close()

        return responses
