from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
import main

app = Flask(__name__)
CORS(app)


@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    data = request.json
    file_url = data['file_url']
    result = main.main(file_url)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)