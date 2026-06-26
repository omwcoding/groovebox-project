from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for frontend development
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "success",
        "message": "Flask backend is running!"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
