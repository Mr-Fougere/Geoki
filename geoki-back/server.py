from flask import Flask, request, jsonify
from confirmadresse import AdresseValidator  # Assurez-vous d'importer votre classe

app = Flask(__name__)
validator = AdresseValidator()

@app.route('/validate_address', methods=['GET'])
def validate_address():
    address = request.args.get('address')
    if not address:
        return jsonify({"error": "No address provided"}), 400
    validation, response = validator.validate_address(address)
    return jsonify({"validation": validation, "response": response})

@app.route('/verify_address', methods=['POST'])
def verify_address():
    data = request.get_json()
    address = data.get('adresse')
    if not address:
        return jsonify({"error": "No address provided"}), 400
    validation, response = validator.validate_address(address)
    return jsonify({"validation": validation, "response": response})


if __name__ == '__main__':
    app.run(debug=True)
