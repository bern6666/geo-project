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
    try:
        nominatim_response = requests.get(nominatim_url, headers=headers)
        nominatim_response.raise_for_status()
        nominatim_data = nominatim_response.json()
        if nominatim_data:
            print(f"Geocoding für {ort}: Erfolgreich")  # Minimale Ausgabe
        else:
            print(f"Geocoding für {ort}: Keine Ergebnisse")
    except requests.RequestException as e:
        print(f"Nominatim Fehler (Wetter): {e}")
        return jsonify({"error": f"Geocoding-Fehler: {str(e)}"}), 500
    
    if not nominatim_data:
        return jsonify({"error": "Ort nicht gefunden. Bitte gib einen genaueren Ortsnamen ein (z.B. 'Berlin, Germany')."}), 404
    
    lat = nominatim_data[0]['lat']
    lon = nominatim_data[0]['lon']
    
    # Schritt 2: Wetterdaten mit OpenWeatherMap
    api_key = OPENWEATHER_API_KEY
    wetter_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&lang=de&appid={api_key}"
    try:
        wetter_response = requests.get(wetter_url)
        wetter_response.raise_for_status()
        wetter_data = wetter_response.json()
        print(f"Wetter für {ort}: Erfolgreich")  # Minimale Ausgabe
    except requests.RequestException as e:
        print(f"Wetter API Fehler: {e}")
        return jsonify({"error": f"Wetter-API-Fehler: {str(e)}"}), 500
    
    return jsonify({
        "ort": ort,
        "koordinaten": {"lat": lat, "lon": lon},
        "wetter": wetter_data
    })

# Route für Streckenberechnung
@app.route('/route/<start>/<ziel>')
def route(start, ziel):
    # Schritt 1: Geocoding für Start und Ziel
    headers = {'User-Agent': 'MeineFlaskApp/1.0'}
    
    # Geocoding für Startort
    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={start}&format=json"
    try:
        start_response = requests.get(nominatim_url, headers=headers)
        start_response.raise_for_status()
        start_data = start_response.json()
        if start_data:
            print(f"Geocoding für Start {start}: Erfolgreich")  # Minimale Ausgabe
        else:
            print(f"Geocoding für Start {start}: Keine Ergebnisse")
    except requests.RequestException as e:
        print(f"Nominatim Fehler (Start): {e}")
        return jsonify({"error": f"Geocoding-Fehler für Startort: {str(e)}"}), 500
    
    if not start_data:
        return jsonify({"error": "Startort nicht gefunden. Bitte gib einen genaueren Ortsnamen ein (z.B. 'Berlin, Germany')."}), 404
    
    # Geocoding für Zielort
    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={ziel}&format=json"
    try:
        ziel_response = requests.get(nominatim_url, headers=headers)
        ziel_response.raise_for_status()
        ziel_data = ziel_response.json()
        if ziel_data:
            print(f"Geocoding für Ziel {ziel}: Erfolgreich")  # Minimale Ausgabe
        else:
            print(f"Geocoding für Ziel {ziel}: Keine Ergebnisse")
    except requests.RequestException as e:
        print(f"Nominatim Fehler (Ziel): {e}")
        return jsonify({"error": f"Geocoding-Fehler für Zielort: {str(e)}"}), 500
    
    if not ziel_data:
        return jsonify({"error": "Zielort nicht gefunden. Bitte gib einen genaueren Ortsnamen ein (z.B. 'Hamburg, Germany')."}), 404
    
    start_lat, start_lon = start_data[0]['lat'], start_data[0]['lon']
    ziel_lat, ziel_lon = ziel_data[0]['lat'], ziel_data[0]['lon']
    
    # Schritt 2: Streckenberechnung mit OSRM
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{ziel_lon},{ziel_lat}?overview=full&geometries=geojson"
    try:
        route_response = requests.get(osrm_url)
        route_response.raise_for_status()
        route_data = route_response.json()
        if route_data.get('code') == 'Ok':
            print(f"Route von {start} nach {ziel}: Erfolgreich")  # Minimale Ausgabe
        else:
            print(f"Route von {start} nach {ziel}: Fehlgeschlagen ({route_data.get('message', 'Unbekannter Fehler')})")
    except requests.RequestException as e:
        print(f"OSRM Fehler: {e}")
        return jsonify({"error": f"Routenberechnungs-Fehler: {str(e)}"}), 500
    
    if route_data.get('code') != 'Ok':
        return jsonify({"error": f"Routenberechnung fehlgeschlagen: {route_data.get('message', 'Unbekannter Fehler')}"}), 400
    
    return jsonify({
        "start": {"ort": start, "lat": start_lat, "lon": start_lon},
        "ziel": {"ort": ziel, "lat": ziel_lat, "lon": ziel_lon},
        "route": route_data['routes'][0]
    })

# Route für die Kartenanzeige
@app.route('/')
def map():
    return render_template('map.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)