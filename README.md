# CompanyTrace UK

A simple web tool to look up UK companies and display their registered address on a map.

- **Input:** Company name or number
- **Output:** Map showing the registered address

**Live site:** https://companytrace-uk.onrender.com  
**Repository:** https://github.com/boragunel/CompanyTrace-UK

---

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/boragunel/CompanyTrace-UK.git
   ```
2. Install dependencies:
   ```
   pip install flask requests gunicorn
   ```
3. Add your Companies House API key in `Website.py`:
   ```python
   COMPANIES_HOUSE_API_KEY = "your-key-here"
   ```
4. Run locally:
   ```
   python Website.py
   ```
5. To deploy changes to the live site:
   ```
   python deploy.py
   ```

---

## How the System Works (End-to-End Flow)

You type a company name or number into the website and click Search. Your browser sends that query to the Flask server running on Render. The Flask server then calls the Companies House API using your API key, fetches the company details, and geocodes the address into coordinates using OpenStreetMap. The results are sent back to your browser which displays the company information and drops a pin on the map.

---

## Components Involved

- **Flask** — serves the website and handles the `/lookup` route on the backend
- **Companies House API** — provides the company data
- **Nominatim (OpenStreetMap)** — converts the registered address into map coordinates
- **Leaflet.js** — renders the interactive map in the browser (loaded from unpkg.com, does not exist in the repository)
- **GitHub & Render** — handle editing, deployment and running of the code. Changes made locally are pushed via `deploy.py`; changes made directly on GitHub do not require `deploy.py`

---

## How Data Moves Between Components

1. User types a query in the browser → request sent to `/lookup?q=tesco` on the Render server
2. Flask calls the Companies House API server-side and gets back company details
3. Flask calls Nominatim with the address to get coordinates
4. Flask bundles everything into a JSON response and sends it back to the browser
5. The browser updates the page and passes the coordinates to Leaflet.js to display the map pin

---

## Where Things Could Break

- **Companies House API key expires or hits rate limit** — if the key is revoked or too many requests are made, all searches will fail
- **Render free tier goes to sleep** — after 15 minutes of inactivity the server sleeps, causing the first request to take ~50 seconds to wake up
- **Nominatim fails** — it's a free OpenStreetMap service which can be slow or return no results for unusual addresses; the geocoder falls back to postcode then country, but the pin may still not appear for very obscure addresses
- **unpkg.com goes down** — this is where `Website.py` loads Leaflet.js from; if it's unavailable the map won't load at all
- **GitHub/Render or local/GitHub synchronization issues** — both links in the deployment chain need to work correctly for website updates to go live