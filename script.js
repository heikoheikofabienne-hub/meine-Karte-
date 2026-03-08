let map;
let markers = [];
let currentEditingId = null;

function initMap() {
    map = L.map('map').setView([51.1657, 10.4515], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    loadFromStorage();
}

async function saveLocation() {
    const data = getFormData();
    if (!data.ort) return alert("Bitte mindestens einen Ort eingeben!");
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(data.strasse + " " + data.ort)}`;
    try {
        const response = await fetch(url);
        const results = await response.json();
        if (results.length > 0) {
            data.id = Date.now();
            data.lat = results[0].lat;
            data.lon = results[0].lon;
            addMarkerToMap(data);
            saveToStorage(data);
            resetForm();
        } else { alert("Ort nicht gefunden!"); }
    } catch (e) { console.error(e); }
}

function addMarkerToMap(data) {
    const icon = L.divIcon({ className: "custom-pin", iconAnchor: [0, 24], popupAnchor: [0, -36], html: `<span style="background-color:${data.farbe}; width:1.5rem; height:1.5rem; display:block; border-radius:50%; border:2px solid white" />` });
    const marker = L.marker([data.lat, data.lon], { icon: icon }).addTo(map);
    marker.bindPopup(`<strong>${data.name}</strong><br>${data.firma}<br>${data.notiz}<div class="popup-btns"><button class="edit-btn" onclick="editMode(${data.id})">Ändern</button><button class="delete-btn" onclick="deletePoint(${data.id})">Löschen</button></div>`);
    marker.id = data.id;
    markers.push(marker);
}

function getFormData() {
    return { name: document.getElementById('name').value, firma: document.getElementById('firma').value, strasse: document.getElementById('strasse').value, ort: document.getElementById('ort').value, datum: document.getElementById('datum').value, notiz: document.getElementById('notiz').value, farbe: document.getElementById('farbe').value };
}

function resetForm() {
    document.querySelectorAll('input, textarea').forEach(el => { if(el.type !== 'file') el.value = ''; });
    document.getElementById('save-btn').style.display = 'block';
    document.getElementById('update-btn').style.display = 'none';
    document.getElementById('cancel-btn').style.display = 'none';
    currentEditingId = null;
}

function saveToStorage(data) {
    let stored = JSON.parse(localStorage.getItem('mapPoints') || '[]');
    stored.push(data);
    localStorage.setItem('mapPoints', JSON.stringify(stored));
}

function loadFromStorage() {
    JSON.parse(localStorage.getItem('mapPoints') || '[]').forEach(data => addMarkerToMap(data));
}

function deletePoint(id) {
    let stored = JSON.parse(localStorage.getItem('mapPoints') || '[]');
    stored = stored.filter(p => p.id !== id);
    localStorage.setItem('mapPoints', JSON.stringify(stored));
    location.reload();
}

function editMode(id) {
    let stored = JSON.parse(localStorage.getItem('mapPoints') || '[]');
    const point = stored.find(p => p.id === id);
    if (point) {
        document.getElementById('name').value = point.name;
        document.getElementById('firma').value = point.firma;
        document.getElementById('strasse').value = point.strasse;
        document.getElementById('ort').value = point.ort;
        document.getElementById('datum').value = point.datum;
        document.getElementById('notiz').value = point.notiz;
        document.getElementById('farbe').value = point.farbe;
        currentEditingId = id;
        document.getElementById('save-btn').style.display = 'none';
        document.getElementById('update-btn').style.display = 'block';
        document.getElementById('cancel-btn').style.display = 'block';
    }
}

async function updateLocation() {
    // 1. Hole alle Daten aus dem Speicher
    let stored = JSON.parse(localStorage.getItem('mapPoints') || '[]');
    
    // 2. Entferne den alten Punkt mit der aktuellen ID
    stored = stored.filter(p => p.id !== currentEditingId);
    
    // 3. Hole die neuen Daten aus dem Formular
    const updatedData = getFormData();
    updatedData.id = currentEditingId; // Wichtig: Die ID muss gleich bleiben
    
    // 4. Geocode-Abfrage für die neuen Daten
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(updatedData.strasse + " " + updatedData.ort)}`;
    try {
        const response = await fetch(url);
        const results = await response.json();
        
        if (results.length > 0) {
            updatedData.lat = results[0].lat;
            updatedData.lon = results[0].lon;
            
            // 5. Neuen Datensatz hinzufügen
            stored.push(updatedData);
            
            // 6. Erst jetzt alles zusammen in den Speicher schreiben
            localStorage.setItem('mapPoints', JSON.stringify(stored));
            
            // 7. Alles zurücksetzen und Seite neu laden
            alert("Änderung gespeichert!");
            location.reload(); 
        } else {
            alert("Ort für das Update nicht gefunden!");
        }
    } catch (e) {
        console.error(e);
        alert("Fehler beim Speichern.");
    }
}
}

// Backup Funktionen
function exportData() {
    const data = localStorage.getItem('mapPoints');
    if (!data) return alert("Keine Daten!");
    const blob = new Blob([data], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'map_backup.json';
    a.click();
}

function importData(event) {
    const reader = new FileReader();
    reader.onload = (e) => { localStorage.setItem('mapPoints', e.target.result); location.reload(); };
    reader.readAsText(event.target.files[0]);
}

window.onload = initMap;
