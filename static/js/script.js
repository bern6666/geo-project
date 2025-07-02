document.addEventListener('DOMContentLoaded', function() {
    // Initialisiere die Karte
    var map = L.map('map', {
        zoomControl: true // Aktiviere standardmäßige Zoom-Buttons
    }).setView([52.5200, 13.4050], 10);

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Globale Variablen für Route und Marker
    var currentRoute = null;
    var currentMarker = null;

    // Benutzerdefinierte Pan-Buttons
    L.Control.PanButtons = L.Control.extend({
        options: { position: 'topright' },
        onAdd: function(map) {
            var container = L.DomUtil.create('div', 'leaflet-control-pan leaflet-bar');
            var directions = [
                { dir: 'up', icon: '↑', delta: [0, -0.01] },
                { dir: 'down', icon: '↓', delta: [0, 0.01] },
                { dir: 'left', icon: '←', delta: [-0.01, 0] },
                { dir: 'right', icon: '→', delta: [0.01, 0] }
            ];

            directions.forEach(function(d) {
                var button = L.DomUtil.create('a', 'leaflet-control-pan-' + d.dir, container);
                button.innerHTML = d.icon;
                button.href = '#';
                L.DomEvent.on(button, 'click', function(e) {
                    e.preventDefault();
                    var center = map.getCenter();
                    map.panTo([center.lat + d.delta[1], center.lng + d.delta[0]]);
                });
            });

            return container;
        }
    });

    L.control.panButtons = function(opts) {
        return new L.Control.PanButtons(opts);
    };
    L.control.panButtons().addTo(map);

    // Wetter abrufen
    window.getWetter = function() {
        var ort = document.getElementById('ort').value;
        var button = document.getElementById('wetter-btn');
        button.classList.add('loading');
        document.getElementById('wetter').innerText = '';
        
        // Entferne bestehenden Marker und Route
        if (currentMarker) {
            map.removeLayer(currentMarker);
            currentMarker = null;
        }
        if (currentRoute) {
            map.removeLayer(currentRoute);
            currentRoute = null;
        }

        fetch(`/wetter-geocode/${ort}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP Fehler ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                button.classList.remove('loading');
                if (data.error) {
                    document.getElementById('wetter').innerText = data.error;
                    return;
                }
                var lat = data.koordinaten.lat;
                var lon = data.koordinaten.lon;
                var wetter = data.wetter.weather[0].description;
                var temp = data.wetter.main.temp;
                document.getElementById('wetter').innerText = `Wetter in ${ort}: ${wetter}, ${temp}\u00B0C`;
                currentMarker = L.marker([lat, lon]).addTo(map)
                    .bindPopup(`${ort}: ${wetter}, ${temp}\u00B0C`)
                    .openPopup();
                map.setView([lat, lon], 10);
            })
            .catch(error => {
                button.classList.remove('loading');
                document.getElementById('wetter').innerText = `Fehler beim Abrufen der Daten: ${error.message}`;
                console.error('Wetter-Fehler:', error);
            });
    };

    // Route berechnen
    window.getRoute = function() {
        var start = document.getElementById('start').value;
        var ziel = document.getElementById('ziel').value;
        var button = document.getElementById('route-btn');
        button.classList.add('loading');
        document.getElementById('route').innerText = '';
        
        // Entferne bestehenden Marker und Route
        if (currentMarker) {
            map.removeLayer(currentMarker);
            currentMarker = null;
        }
        if (currentRoute) {
            map.removeLayer(currentRoute);
            currentRoute = null;
        }

        fetch(`/route/${start}/${ziel}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP Fehler ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                button.classList.remove('loading');
                if (data.error) {
                    document.getElementById('route').innerText = data.error;
                    return;
                }
                var distance = (data.route.distance / 1000).toFixed(2);
                var duration = (data.route.duration / 60).toFixed(1);
                document.getElementById('route').innerText = `Route von ${start} nach ${ziel}: ${distance} km, ${duration} min`;
                var coords = data.route.geometry.coordinates.map(c => [c[1], c[0]]);
                currentRoute = L.polyline(coords, {color: 'blue'}).addTo(map);
                map.fitBounds(coords);
            })
            .catch(error => {
                button.classList.remove('loading');
                document.getElementById('route').innerText = `Fehler beim Abrufen der Route: ${error.message}`;
                console.error('Routen-Fehler:', error);
            });
    };

    // Dark Mode umschalten
    window.toggleDarkMode = function() {
        document.querySelector('.sidebar').classList.toggle('dark-mode');
    };
});