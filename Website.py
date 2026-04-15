from flask import Flask, render_template_string, request, jsonify
import requests

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
let map = null;
let marker = null;

async function lookup() {
    const query = document.getElementById('query').value.trim();
    if (!query) return;

    document.getElementById('error').style.display = 'none';
    document.getElementById('result').style.display = 'none';
    document.getElementById('loading').style.display = 'block';

    try {
        const response = await fetch('/lookup?q=' + encodeURIComponent(query));
        const data = await response.json();
        document.getElementById('loading').style.display = 'none';

        if (data.error) {
            document.getElementById('error').textContent = data.error;
            document.getElementById('error').style.display = 'block';
            return;
        }

        document.getElementById('companyName').textContent = data.name;
        document.getElementById('companyNumber').textContent = data.number;
        document.getElementById('companyType').textContent = data.type;
        document.getElementById('incorporated').textContent = data.incorporated || 'N/A';
        document.getElementById('address').textContent = data.address;

        const badge = document.getElementById('statusBadge');
        badge.textContent = data.status;
        badge.className = 'badge ' + (data.status.toLowerCase().includes('active') ? 'active' : data.status.toLowerCase().includes('dissolved') ? 'dissolved' : 'other');

        document.getElementById('result').style.display = 'block';

        if (data.lat && data.lng) {
            if (!map) {
                map = L.map('map').setView([data.lat, data.lng], 15);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
            } else {
                map.setView([data.lat, data.lng], 15);
                if (marker) map.removeLayer(marker);
            }
            marker = L.marker([data.lat, data.lng]).addTo(map)
                .bindPopup('<b>' + data.name + '</b><br>' + data.address).openPopup();
        }

    } catch (e) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').textContent = 'Something went wrong. Please try again.';
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

def geocode_address(address):
    headers = {"User-Agent": "CompanyTraceUK/1.0"}
    # Try full address first, then fall back to just postcode
    queries = [address]
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 2:
        queries.append(parts[-2] + ", " + parts[-1])  # postcode + country
    queries.append(parts[-1])  # just country as last resort

    for query in queries:
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": query, "format": "json", "limit": 1, "countrycodes": "gb"}
            r = requests.get(url, params=params, headers=headers, timeout=5)
            results = r.json()
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
        except:
            pass
    return None, None


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/lookup")
def lookup():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Please enter a company name or number."})

    auth = (COMPANIES_HOUSE_API_KEY, "")

    # Try direct company number lookup first
    r = requests.get(
        f"https://api.company-information.service.gov.uk/company/{query.upper()}",
        auth=auth, timeout=10
    )
    if r.status_code == 200:
        data = r.json()
    else:
        # Fall back to name search
        r = requests.get(
            "https://api.company-information.service.gov.uk/search/companies",
            params={"q": query, "items_per_page": 1},
            auth=auth, timeout=10
        )
        if r.status_code != 200 or not r.json().get("items"):
            return jsonify({"error": "Company not found. Try a different name or number."})
        # Get full details
        company_number = r.json()["items"][0]["company_number"]
        r2 = requests.get(
            f"https://api.company-information.service.gov.uk/company/{company_number}",
            auth=auth, timeout=10
        )
        data = r2.json()

    addr = data.get("registered_office_address") or {}
    address_parts = [
        addr.get("address_line_1", ""),
        addr.get("address_line_2", ""),
        addr.get("locality", ""),
        addr.get("region", ""),
        addr.get("postal_code", ""),
        addr.get("country", ""),
    ]
    address_str = ", ".join(p for p in address_parts if p)

    lat, lng = geocode_address(address_str)

    return jsonify({
        "name": data.get("company_name", "Unknown"),
        "number": data.get("company_number", "N/A"),
        "type": (data.get("company_type") or data.get("type", "N/A")).replace("-", " ").title(),
        "status": data.get("company_status", "Unknown").replace("-", " ").title(),
        "incorporated": data.get("date_of_creation", ""),
        "address": address_str or "Address not available",
        "lat": lat,
        "lng": lng,
    })