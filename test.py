from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from app import app
app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint for IBM Code Engine"""
    return jsonify({"status": "healthy", "service": "weather-api"}), 200

@app.route("/getWeather", methods=["GET", "POST"])
def get_weather():
    """Get weather information for a specified city"""
    try:
        # Get city from query parameter or request body
        if request.method == "GET":
            city = request.args.get("city", "tokyo")
        else:  # POST
            data = request.get_json() or {}
            city = data.get("city", "tokyo")
        
        # Get API key from environment variable
        API_KEY = os.environ.get("WEATHER_API_KEY", "")
        
        if not API_KEY:
            return jsonify({"error": "Weather API key not configured"}), 500
        
        # Direct URL formatting with f-string
        url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&lang=en"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 400:
            return jsonify({"error": f"City '{city}' not found"}), 404
        elif response.status_code == 401:
            return jsonify({"error": "Invalid API key"}), 401
        elif response.status_code != 200:
            return jsonify({"error": f"Weather API error: {response.status_code}"}), 500

        weather_data = response.json()
        
        # More robust data validation
        if "current" not in weather_data or "condition" not in weather_data["current"]:
            return jsonify({"error": "Invalid response from weather API"}), 500

        return jsonify({
            "city": weather_data.get("location", {}).get("name", city),
            "region": weather_data.get("location", {}).get("region", ""),
            "country": weather_data.get("location", {}).get("country", ""),
            "condition": weather_data["current"]["condition"]["text"],
            "temperature_c": weather_data["current"]["temp_c"],
            "temperature_f": weather_data["current"]["temp_f"],
            "humidity": weather_data["current"]["humidity"],
            "wind_kph": weather_data["current"]["wind_kph"],
            "wind_mph": weather_data["current"]["wind_mph"],
            "last_updated": weather_data["current"]["last_updated"]
        })
        
    except requests.RequestException as e:
        return jsonify({"error": "Network error occurred"}), 503
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)