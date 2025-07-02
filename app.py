from flask import Flask, jsonify, render_template, request
import requests
import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if OPENWEATHER_API_KEY:
    os.environ["OPENWEATHER_API_TOKEN"] = OPENWEATHER_API_KEY
else:
    print("⚠️ WARNUNG: Kein OPENWEATHER_API_KEY in .env gefunden!")

app = Flask(__name__)

# Route für Geocoding und Wetter
@app.route('/wetter-geocode/<ort>')
def wetter_geocode(ort):
    # Schritt 1: Geocoding mit Nominatim
    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={ort}&format=json"
    headers = {'User-Agent': 'MeineFlaskApp/1.0'}
    nominatim_response = requests.get(nominatim_url, headers=headers).json()
    
    if not nominatim_response:
        return jsonify({"error": "Ort nicht gefunden"}), 404
    
    lat = nominatim_response[0]['lat']
    lon = nominatim_response[0]['lon']
    
    # Schritt 2: Wetterdaten mit OpenWeatherMap
    api_key = OPENWEATHER_API_KEY
    wetter_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&lang=de&appid={api_key}"
    wetter_response = requests.get(wetter_url).json()
    
    return jsonify({
        "ort": ort,
        "koordinaten": {"lat": lat, "lon": lon},
        "wetter": wetter_response
    })

# Route für Streckenberechnung
@app.route('/route/<start>/<ziel>')
def route(start, ziel):
    # Schritt 1: Geocoding für Start und Ziel
    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={start}&format=json"
    headers = {'User-Agent': 'MeineFlaskApp/1.0'}
    start_data = requests.get(nominatim_url, headers=headers).json()
    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={ziel}&format=json"
    ziel_data = requests.get(nominatim_url, headers=headers).json()
    
    if not start_data or not ziel_data:
        return jsonify({"error": "Start- oder Zielort nicht gefunden"}), 404
    
    start_lat, start_lon = start_data[0]['lat'], start_data[0]['lon']
    ziel_lat, ziel_lon = ziel_data[0]['lat'], ziel_data[0]['lon']
    
    # Schritt 2: Streckenberechnung mit OSRM
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{ziel_lon},{ziel_lat}?overview=full&geometries=geojson"
    route_response = requests.get(osrm_url).json()
    
    if route_response.get('code') != 'Ok':
        return jsonify({"error": "Route konnte nicht berechnet werden"}), 400
    
    return jsonify({
        "start": {"ort": start, "lat": start_lat, "lon": start_lon},
        "ziel": {"ort": ziel, "lat": ziel_lat, "lon": ziel_lon},
        "route": route_response['routes'][0]
    })

# Route für die Kartenanzeige
@app.route('/')
def map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)