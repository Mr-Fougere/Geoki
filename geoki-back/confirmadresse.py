import requests
import json

class AdresseValidator:
    BASE_URL = "https://api-adresse.data.gouv.fr/search/"

    def __init__(self, radius=10):
        self.radius = radius

    def _make_request(self, query, type="housenumber"):
        params = {
            "q": query,
            "type": type,
            "autocomplete": 1
        }
        response = requests.get(self.BASE_URL, params=params)
        return response.json()

    def validate_address(self, address):
        response = self._make_request(address, "housenumber")
        if response["features"]:  # Vérifie si la liste des résultats n'est pas vide
            return "L'adresse est valide", response
        else:
            return "L'adresse n'est pas valide", self.suggest_address(address)

    def suggest_address(self, address):
        street_suggestions = self._make_request(address, "street")
        municipality_suggestions = self._make_request(address, "municipality")
        return {
            "streets": street_suggestions,
            "municipalities": municipality_suggestions
        }

    def get_coordinates_json(self, address):
        response = self._make_request(address, "housenumber")
        if response["features"]:
            coordinates = response["features"][0]["geometry"]["coordinates"]
            return json.dumps({
                "longitude": coordinates[0],
                "latitude": coordinates[1],
                "radius": self.radius
            })
        else:
            return None

# Exemple d'utilisation
validator = AdresseValidator()
print(validator.validate_address("12 rue faubourg saint antoine 75012"))
print(validator.get_coordinates_json("12 rue faubourg saint antoine 75012"))
