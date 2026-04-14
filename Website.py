from flask import Flask, render_template_string

app = Flask(__name__)

COMPANIES_HOUSE_API_KEY = "603721d2-01d8-42be-87bf-a0ed840f979f"

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CompanyTrace UK</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f4f6f9; color: #222; }

        header { background: #1a2e4a; color: white; padding: 24px 40px; }
        header h1 { font-size: 1.6rem; letter-spacing: 1px; }
        header span { font-size: 0.9rem; color: #8fa8c8; margin-top: 4px; display: block; }

        .container { max-width: 900px; margin: 40px auto; padding: 0 20px; }

        .search-box { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 30px; }
        .search-box label { font-weight: 600; font-size: 0.95rem; color: #444; display: block; margin-bottom: 10px; }
        .input-row { display: flex; gap: 12px; }
        .input-row input { flex: 1; padding: 13px 18px; border: 2px solid #dde3ec; border-radius: 7px; font-size: 1rem; outline: none; transition: border 0.3s; }
        .input-row input:focus { border-color: #1a2e4a; }
        .input-row button { padding: 13px 28px; background: #1a2e4a; color: white; border: none; border-radius: 7px; font-size: 1rem; cursor: pointer; transition: background 0.3s; }
        .input-row button:hover { background: #2a4a72; }

        .result-card { background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); margin-bottom: 30px; display: none; }
        .result-card h2 { font-size: 1.4rem; color: #1a2e4a; margin-bottom: 6px; }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; margin-bottom: 20px; }
        .badge.active { background: #e0f7ea; color: #1b7a3e; }
        .badge.dissolved { background: #fdecea; color: #b71c1c; }
        .badge.other { background: #e8eaf6; color: #3949ab; }

        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
        .info-item label { font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 4px; }
        .info-item p { font-size: 1rem; color: #222; font-weight: 500; }

        #map { height: 380px; border-radius: 8px; border: 1px solid #dde3ec; }

        .error-box { background: #fdecea; border: 1px solid #f5c6c6; color: #b71c1c; padding: 14px 18px; border-radius: 7px; display: none; margin-top: 14px; }
        .loading { text-align: center; color: #888; padding: 14px; display: none; }
    </style>
</head>
<body>

<header>
    <h1>CompanyTrace UK</h1>
    <span>Search UK companies via Companies House</span>
</header>

<div class="container">
    <div class="search-box">
        <label>Enter company name or number</label>
        <div class="input-row">
            <input type="text" id="query" placeholder="e.g. Tesco PLC or 00445790" />
            <button onclick="lookup()">Search</button>
        </div>
        <div class="error-box" id="error"></div>
        <div class="loading" id="loading">Looking up company...</div>
    </div>

    <div class="result-card" id="result">
        <h2 id="companyName"></h2>
        <span class="badge" id="statusBadge"></span>
        <div class="info-grid">
            <div class="info-item"><label>Company Number</label><p id="companyNumber"></p></div>
            <div class="info-item"><label>Company Type</label><p id="companyType"></p></div>
            <div class="info-item"><label>Incorporated</label><p id="incorporated"></p></div>
            <div class="info-item"><label>Registered Address</label><p id="address"></p></div>
        </div>
        <div id="map"></div>
    </div>
</div>

<script>
const API_KEY = "{{ api_key }}";
let map = null;
let marker = null;

async function lookup() {
    const query = document.getElementById('query').value.trim();
    if (!query) return;

    document.getElementById('error').style.display = 'none';
    document.getElementById('result').style.display = 'none';
    document.getElementById('loading').style.display = 'block';

    const headers = {
        "Authorization": "Basic " + btoa(API_KEY + ":")
    };

    try {
        let data;

        // Try direct number lookup first
        const directRes = await fetch(
            `https://api.company-information.service.gov.uk/company/${query.toUpperCase()}`,
            { headers }
        );

        if (directRes.ok) {
            data = await directRes.json();
        } else {
            // Fall back to name search
            const searchRes = await fetch(
                `https://api.company-information.service.gov.uk/search/companies?q=${encodeURIComponent(query)}&items_per_page=1`,
                { headers }
            );
            const searchData = await searchRes.json();
            if (!searchData.items || searchData.items.length === 0) {
                throw new Error("Company not found.");
            }
            // Get full company details
            const companyNumber = searchData.items[0].company_number;
            const detailRes = await fetch(
                `https://api.company-information.service.gov.uk/company/${companyNumber}`,
                { headers }
            );
            data = await detailRes.json();
        }

        document.getElementById('loading').style.display = 'none';

        const addr = data.registered_office_address || {};
        const addressParts = [
            addr.address_line_1, addr.address_line_2,
            addr.locality, addr.region, addr.postal_code, addr.country
        ].filter(Boolean);
        const addressStr = addressParts.join(", ") || "Address not available";

        document.getElementById('companyName').textContent = data.company_name || "Unknown";
        document.getElementById('companyNumber').textContent = data.company_number || "N/A";
        document.getElementById('companyType').textContent = (data.company_type || "N/A").replace(/-/g, " ");
        document.getElementById('incorporated').textContent = data.date_of_creation || "N/A";
        document.getElementById('address').textContent = addressStr;

        const status = (data.company_status || "unknown").replace(/-/g, " ");
        const badge = document.getElementById('statusBadge');
        badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        badge.className = 'badge ' + (status.includes('active') ? 'active' : status.includes('dissolved') ? 'dissolved' : 'other');

        document.getElementById('result').style.display = 'block';

        // Geocode with Nominatim
        const geoRes = await fetch(
            `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(addressStr)}&format=json&limit=1`,
            { headers: { "User-Agent": "CompanyTraceUK/1.0" } }
        );
        const geoData = await geoRes.json();

        if (geoData.length > 0) {
            const lat = parseFloat(geoData[0].lat);
            const lng = parseFloat(geoData[0].lon);

            if (!map) {
                map = L.map('map').setView([lat, lng], 15);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
            } else {
                map.setView([lat, lng], 15);
                if (marker) map.removeLayer(marker);
            }
            marker = L.marker([lat, lng]).addTo(map)
                .bindPopup('<b>' + (data.company_name || '') + '</b><br>' + addressStr).openPopup();
        }

    } catch (e) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').textContent = e.message || 'Something went wrong. Please try again.';
        document.getElementById('error').style.display = 'block';
    }
}

document.getElementById('query').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') lookup();
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML, api_key=COMPANIES_HOUSE_API_KEY)