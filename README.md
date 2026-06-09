# 🛡️ AeroShield
### Environmental & Population Risk Assessment System

AeroShield is an AI-powered emergency risk assessment agent that helps emergency managers and first responders evaluate the impact of hazardous events — wildfires, chemical spills, explosions, tornadoes, floods, and more — in real time.

Built for the **Google Cloud Rapid Agent Hackathon** using **Vertex AI Agent Builder (Gemini 2.5 Flash)** and **Elasticsearch (via MCP)**.

---

## 🌐 Live Demo
**https://aeroshield-281390590909.us-central1.run.app/aeroshield**

---

## 🏗️ Architecture

```
User (Web UI)
     │
     ▼
AeroShield Frontend (HTML/Leaflet — Cloud Run)
     │
     ▼
Google ADK Agent — Gemini 2.5 Flash (Cloud Run)
     │
     ├── geocode_location        → OpenStreetMap Nominatim
     ├── search_population_data  → Elasticsearch (83,047 US Census Tracts)
     ├── search_hazmat_facilities→ Elasticsearch (hazmat infrastructure index)
     ├── search_incident_history → Elasticsearch (historical incidents index)
     ├── get_weather_conditions  → Open-Meteo API (live wind/weather)
     ├── calculate_plume_model   → Gaussian plume cone → GeoJSON
     └── calculate_risk_score    → Weighted risk formula → tier + evac radius
```

---

## ✨ Features

- **Any location** — geocodes city names, addresses, landmarks, schools, hospitals, and businesses
- **Census tract precision** — 83,047 US census tracts loaded from the 2020 Census for neighborhood-level population accuracy
- **Live weather** — fetches real-time wind speed and direction from Open-Meteo, no API key required
- **Hazmat detection** — identifies nearby hazardous material facilities within the affected radius
- **Historical context** — surfaces similar past incidents from the same region
- **Plume modeling** — computes a wind-driven Gaussian plume cone and renders it as GeoJSON on an interactive Leaflet map
- **Risk scoring** — weighted formula: population exposure (40%) + hazmat proximity (35%) + event severity (25%) + wind modifier
- **Evacuation routing** — recommends specific cardinal directions away from the plume and hazmat facilities
- **Live thinking status** — UI shows each tool step as it executes (geocoding → population → hazmat → weather → plume → score)

---

## 🗂️ Project Structure

```
aeroshield/
├── app/
│   ├── agent.py              # ADK agent — all tools and system prompt
│   ├── fast_api_app.py       # FastAPI backend + static file serving
│   ├── static/
│   │   └── index.html        # AeroShield frontend (chat + Leaflet map)
│   └── app_utils/            # Telemetry and typing utilities
├── elastic_setup.py          # Initial Elasticsearch index setup + seed data
├── elastic_census_seed.py    # 2020 Census tract loader (all 50 states)
├── Dockerfile                # Cloud Run container
├── pyproject.toml            # Python dependencies
└── README.md
```

---

## 🚀 Setup & Deployment

### Prerequisites
- Python 3.11+
- Google Cloud SDK (`gcloud`)
- `uv` package manager
- Elasticsearch deployment (Elastic Cloud)
- GCP project with Vertex AI, Cloud Run, and Secret Manager enabled

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/aeroshield.git
cd aeroshield
agents-cli install
```

### 2. Store secrets in GCP Secret Manager
```bash
echo -n "YOUR_ELASTIC_API_KEY" | gcloud secrets create elastic-api-key --data-file=- --replication-policy="automatic"
echo -n "YOUR_ELASTIC_URL" | gcloud secrets create elastic-url --data-file=- --replication-policy="automatic"
```

### 3. Seed Elasticsearch
```bash
# Initial indexes + sample hazmat/incident data
uv run python3 elastic_setup.py

# Full US Census tract population data (83,047 tracts, ~30 min)
CENSUS_API_KEY="your_key" uv run python3 elastic_census_seed.py
```
Get a free Census API key at: https://api.census.gov/data/key_signup.html

### 4. Run locally
```bash
ELASTIC_API_KEY="your_key" agents-cli playground
# Frontend: cd app/static && python3 -m http.server 3000
```

### 5. Deploy to Cloud Run
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT \
  --member="serviceAccount:YOUR_SA@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

agents-cli deploy --project YOUR_PROJECT --no-confirm-project

gcloud run services add-iam-policy-binding aeroshield \
  --region=us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

---

## 🧪 Example Scenarios

| Prompt | What AeroShield does |
|--------|----------------------|
| `Chemical spill near Texas Children's Hospital, Houston — severity 6` | Geocodes the hospital, queries ~48k nearby residents, finds Gulf Coast Refinery, fetches live wind, models southward plume |
| `Wildfire near Dodger Stadium, Los Angeles — severity 8` | Identifies 174k exposed residents, LA Harbor Fuel Terminal, models ENE plume driven by live wind |
| `Tornado near Moore High School, Oklahoma — severity 8` | Historical context: multiple past tornadoes in the area, risk assessment with evacuation routing |
| `Gas explosion near Times Square, New York — severity 7` | Dense urban assessment, blast radius modeling, evacuation away from Times Square |

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Agent | Google ADK + Gemini 2.5 Flash (Vertex AI) |
| Partner Integration | Elasticsearch (Elastic Cloud) via MCP |
| Population Data | 2020 US Census API — 83,047 tracts |
| Geocoding | OpenStreetMap Nominatim |
| Weather | Open-Meteo API |
| Mapping | Leaflet.js + OpenStreetMap |
| Backend | FastAPI + Cloud Run |
| Secrets | GCP Secret Manager |
| CI/CD | Google Cloud Build |

---

## ⚠️ Disclaimer

AeroShield is a decision-support tool for trained emergency personnel. Risk assessments are based on available data and should not be used as the sole basis for emergency response decisions. Outputs do not constitute official emergency orders or government directives.

---

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE)