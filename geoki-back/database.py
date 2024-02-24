from datetime import datetime
from flask_socketio import SocketIO
import requests
import gzip
import re
import csv
import pyodbc 

# Establish a connection to the database

DEPARTMENT_ADRESSES_CSV = "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-"
ADRESS_ROW_SIZE = 23
LAT_COL= 13
LON_COL = 12
POSTAL_CODE_COL = 5
INSEE_CODE_COL = 6
STREET_COL = 4
NUMBER_COL = 2
SUBDIVISION_COL = 3
TOWN_COL = 7
IGNORED_WORDS = ["le", "la", "les", "des", "de", "du", "un", "une", "au", "aux", "ce", "cette", "ces", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "notre", "nos", "votre", "vos", "leur", "leurs"]

class Database:
    def __init__(self, socket: SocketIO):
        self.conn = None
        self.cursor = None
        self.socket = socket
        self.open_connection()
        self.create_tables()
        self.close()

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
        self.create_street_table()
        self.create_addresses_table()
        self.create_point_of_interest_table()
        self.create_dictionary_table()
        self.create_dictionary_references_table()
        self.commit()

    def create_street_table(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'street')
            BEGIN
                CREATE TABLE street (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    town NVARCHAR(255) NOT NULL,
                    postal_code NVARCHAR(255) NOT NULL,
                    insee_code NVARCHAR(255),
                    name NVARCHAR(255) NOT NULL
                );
            END
        ''')

    def create_addresses_table(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'address')
            BEGIN
                CREATE TABLE address (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    street_id INT NOT NULL,
                    number NVARCHAR(255) NOT NULL,
                    subdivision NVARCHAR(255),
                    habitation_type NVARCHAR(255),
                    longitude FLOAT,
                    latitude FLOAT,
                    FOREIGN KEY (street_id) REFERENCES Street (id)
                );
            END
        ''')

    def create_point_of_interest_table(self):
        self.cursor.execute('''
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'point_of_interest')
            BEGIN
                CREATE TABLE point_of_interest (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    name NVARCHAR(255) NOT NULL,
                    type NVARCHAR(255) NOT NULL,
                    address_id INT NOT NULL,
                    FOREIGN KEY (address_id) REFERENCES Address (id)
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
                    reference_type NVARCHAR(255) NOT NULL,
                    FOREIGN KEY (dictionary_id) REFERENCES Dictionnary (id)
                );
            END
        ''')

    def create_indexes(self):
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_town ON street (town)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON dictionnary (word)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_postal ON street (postal_code)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_insee ON street (insee_code)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_dic ON dictionnary_reference (dictionary_id)")

    def fetch_departments_adresses(self, departments: list):
        for department in departments:
            try:
                department_number = int(department)
                print(f"Department number: {department_number}")
                self.fetch_one_department_adresses(department_number)
            except ValueError:
                print(f"Invalid department number: {department}")

    def fetch_one_department_adresses(self, department: int):
        department_number = str(department).zfill(2)
        department_file =  f"{DEPARTMENT_ADRESSES_CSV}{department_number}.csv.gz"
        response = requests.get(department_file)
        with open(f"downloads/{department_number}.csv.gz", "wb") as f:
            f.write(response.content)

        with gzip.open(f"downloads/{department_number}.csv.gz", "rb") as f_in:
            with open(f"converts/{department_number}.csv", "wb") as f_out:
                f_out.write(f_in.read())

        total_lines = 0
        with open(f"converts/{department_number}.csv", "r", encoding="utf-8") as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                total_lines += 1

        self.socket.emit('fetching_infos', {'total_lines': total_lines})
        self.open_connection()
        self.parse_csv(department_number, total_lines)
        self.close()

    def parse_csv(self,department_number,total_lines):
        with open(f"converts/{department_number}.csv", "r", encoding="utf-8") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';')
            next(csvreader)
            current_line = 0
            for row in csvreader:
                current_line += 1
                adresse_id = self.insert_address(row)
                print(f"{current_line}/{total_lines}")
                self.insert_in_dictionary(row, adresse_id, "adress")
                self.commit()

    def insert_address(self, row):
        if len(row) != ADRESS_ROW_SIZE:
            return
        street_id = self.get_or_create_street(row)
        self.cursor.execute('''INSERT INTO address (street_id, number, subdivision, longitude, latitude, habitation_type) output inserted.ID 
                    VALUES (?, ?, ?, ?, ?, ?)''', (street_id, row[NUMBER_COL], row[SUBDIVISION_COL], row[LON_COL], row[LAT_COL], None))
        last_row_id = self.cursor.fetchone()[0]
    
        return last_row_id

    def get_or_create_street(self, row):
        street_name = row[STREET_COL]
        postal_code = row[POSTAL_CODE_COL]
        town = row[TOWN_COL]
        self.cursor.execute("SELECT id FROM street WHERE name = ? AND postal_code = ? AND town = ?", (street_name, postal_code, town))
        existing_street = self.cursor.fetchone()
        if existing_street:
            return existing_street[0] 
        else:
            insee = row[INSEE_CODE_COL]
            self.cursor.execute('''INSERT INTO street (name, postal_code, town, insee_code) output inserted.ID 
                                VALUES (?, ?, ?, ?)''', (street_name, postal_code, town, insee))
            last_row_id = self.cursor.fetchone()[0]
            return last_row_id

        
    def split_street_name(self, street_name):
        return re.split(r'[\s_\'°-]', street_name)
        
    def filter_words(self, words):
        filtered_words = []
        for word in words:
            word = word.lower()
            if len(word) >= 2 and not word.isdigit() and word not in IGNORED_WORDS:
                filtered_words.append(word)
        return filtered_words

    def insert_in_dictionary(self, row, reference_id, reference_type):
        filtered_words = self.filter_words(self.split_street_name( row[STREET_COL]) + self.split_street_name( row[TOWN_COL]))
        for word in filtered_words:
            self.cursor.execute("SELECT id FROM dictionnary WHERE word = ?", (word,))
            existing_word = self.cursor.fetchone()
            if existing_word:
                self.cursor.execute('''
                    INSERT INTO dictionnary_reference (dictionary_id, reference_id, reference_type)
                    VALUES (?, ?, ?)''',
                    (existing_word[0], reference_id,reference_type ))
            else:
                self.cursor.execute('''
                    INSERT INTO dictionnary (word)
                    output inserted.ID 
                    VALUES (?)''',
                    (word,))
                dictionary_id = self.cursor.fetchone()[0]
                
                self.cursor.execute('''
                    INSERT INTO dictionnary_reference (dictionary_id, reference_id, reference_type)
                    VALUES (?, ?, ?  )''',
                    (dictionary_id, reference_id, reference_type ))

    def find_addresses_by_keywords(self, search_criteria):
        self.open_connection()
        search_street = search_criteria.get("street", "")
        search_number = search_criteria.get("number")
        search_town = search_criteria.get("town")

        street_keywords = self.filter_words(self.split_street_name( search_street))
        references = []
        for keyword in street_keywords:
            self.cursor.execute('''
                SELECT reference_id FROM DictionnaryReference
                INNER JOIN Dictionnary ON DictionnaryReference.dictionary_id = Dictionnary.id
                WHERE Dictionnary.word = ?
            ''', (keyword,))
            result = self.cursor.fetchall()
            references.extend(result)

        references = [reference[0] for reference in references]

        grouped_references = {}
        for reference in references:
            grouped_references[reference] = grouped_references.get(reference, 0) + 1
        sorted_references = sorted(grouped_references.items(), key=lambda x: x[1], reverse=True)
        print(grouped_references)
        addresses = []

        for reference_id, _ in sorted_references:
            print(reference_id)
            reference_id = int(reference_id) 
            self.cursor.execute("SELECT town, number FROM Adresse WHERE id = ?", (reference_id,))
            result = self.cursor.fetchone()
            if result:
                town, number = result
                if (not town or town.lower() == reference_town.lower()) and (not search_number or search_number == reference_number):
                    self.cursor.execute("SELECT street FROM Adresse WHERE id = ?", (reference_id,))
                    street_result = self.cursor.fetchone()
                    if street_result and street_result[0] not in [address.get("street") for address in addresses]:
                        self.cursor.execute("SELECT * FROM Adresse WHERE id = ?", (reference_id,))
                        address_result = self.cursor.fetchone()
                        addresses.append(address_result)

            if len(addresses) >= 20:
                break

        self.close()
        return addresses
