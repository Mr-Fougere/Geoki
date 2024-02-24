import requests
import json

class ResourceFetcher:
    def __init__(self):
        self.resources = self.load_config()

    def load_config(self):
        try:
            with open( "config.json", 'r') as f:
                config_data = json.load(f)
                return config_data.get('resources', [])
        except Exception as e:
            print("An error occurred while loading config:", e)
            return []

    def get_file_url(self, resource_name):
        for resource in self.resources:
            if resource.get('resource_name') == resource_name:
                return resource.get('url_file')
        return None
    
    def fetch_resource_file(self, resource_name):
        try:
            response = requests.get(self.get_file_url(resource_name))
            if response.status_code == 200:
                return response.content
            else:
                return None
        except Exception as e:
            print("An error occurred while fetching file URL:", e)
            return None