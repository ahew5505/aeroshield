"""
AeroShield - Elasticsearch index setup and seed data loader.
Run once to initialize your Elastic deployment.
"""
import os
from elasticsearch import Elasticsearch

ELASTIC_URL = os.environ.get("ELASTIC_URL", "https://my-elasticsearch-project-da6e0d.es.us-central1.gcp.elastic.cloud:443")
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY", "")

es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

# ── Index Mappings ────────────────────────────────────────────────────────────

MAPPINGS = {
    "population_density": {
        "mappings": {
            "properties": {
                "city":               {"type": "keyword"},
                "county":             {"type": "keyword"},
                "state":              {"type": "keyword"},
                "population":         {"type": "integer"},
                "density_per_sq_mile":{"type": "float"},
                "location":           {"type": "geo_point"},
            }
        }
    },
    "hazmat_infrastructure": {
        "mappings": {
            "properties": {
                "facility_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "facility_type": {"type": "keyword"},
                "hazmat_class":  {"type": "keyword"},
                "risk_tier":     {"type": "keyword"},
                "location":      {"type": "geo_point"},
            }
        }
    },
    "incident_history": {
        "mappings": {
            "properties": {
                "event_type":            {"type": "keyword"},
                "date":                  {"type": "date"},
                "severity":              {"type": "integer"},
                "affected_radius_miles": {"type": "float"},
                "casualties":            {"type": "integer"},
                "location":              {"type": "geo_point"},
            }
        }
    },
}

# ── Seed Data ─────────────────────────────────────────────────────────────────

POPULATION_DATA = [
    {"city": "Houston",      "county": "Harris",      "state": "TX", "population": 2304580, "density_per_sq_mile": 3613, "location": {"lat": 29.7604, "lon": -95.3698}},
    {"city": "Phoenix",      "county": "Maricopa",    "state": "AZ", "population": 1608139, "density_per_sq_mile": 3120, "location": {"lat": 33.4484, "lon": -112.0740}},
    {"city": "San Antonio",  "county": "Bexar",       "state": "TX", "population": 1434625, "density_per_sq_mile": 3238, "location": {"lat": 29.4241, "lon": -98.4936}},
    {"city": "Dallas",       "county": "Dallas",      "state": "TX", "population": 1304379, "density_per_sq_mile": 3944, "location": {"lat": 32.7767, "lon": -96.7970}},
    {"city": "Los Angeles",  "county": "Los Angeles", "state": "CA", "population": 3898747, "density_per_sq_mile": 8092, "location": {"lat": 34.0522, "lon": -118.2437}},
    {"city": "Chicago",      "county": "Cook",        "state": "IL", "population": 2696555, "density_per_sq_mile": 11900, "location": {"lat": 41.8781, "lon": -87.6298}},
    {"city": "Jacksonville", "county": "Duval",       "state": "FL", "population": 949611,  "density_per_sq_mile": 1214, "location": {"lat": 30.3322, "lon": -81.6557}},
    {"city": "Columbus",     "county": "Franklin",    "state": "OH", "population": 905748,  "density_per_sq_mile": 4015, "location": {"lat": 39.9612, "lon": -82.9988}},
    {"city": "Austin",       "county": "Travis",      "state": "TX", "population": 978908,  "density_per_sq_mile": 3079, "location": {"lat": 30.2672, "lon": -97.7431}},
    {"city": "Memphis",      "county": "Shelby",      "state": "TN", "population": 633104,  "density_per_sq_mile": 2076, "location": {"lat": 35.1495, "lon": -90.0490}},
    {"city": "Louisville",   "county": "Jefferson",   "state": "KY", "population": 633045,  "density_per_sq_mile": 1795, "location": {"lat": 38.2527, "lon": -85.7585}},
    {"city": "Baltimore",    "county": "Baltimore",   "state": "MD", "population": 585708,  "density_per_sq_mile": 7671, "location": {"lat": 39.2904, "lon": -76.6122}},
    {"city": "Oklahoma City","county": "Oklahoma",    "state": "OK", "population": 695042,  "density_per_sq_mile": 1044, "location": {"lat": 35.4676, "lon": -97.5164}},
    {"city": "Tulsa",        "county": "Tulsa",       "state": "OK", "population": 413066,  "density_per_sq_mile": 2014, "location": {"lat": 36.1540, "lon": -95.9928}},
    {"city": "New Orleans",  "county": "Orleans",     "state": "LA", "population": 383997,  "density_per_sq_mile": 2082, "location": {"lat": 29.9511, "lon": -90.0715}},
    {"city": "Tampa",        "county": "Hillsborough","state": "FL", "population": 399700,  "density_per_sq_mile": 3198, "location": {"lat": 27.9506, "lon": -82.4572}},
    {"city": "Denver",       "county": "Denver",      "state": "CO", "population": 715522,  "density_per_sq_mile": 4493, "location": {"lat": 39.7392, "lon": -104.9903}},
    {"city": "Portland",     "county": "Multnomah",   "state": "OR", "population": 652503,  "density_per_sq_mile": 4375, "location": {"lat": 45.5051, "lon": -122.6750}},
    {"city": "Las Vegas",    "county": "Clark",       "state": "NV", "population": 641903,  "density_per_sq_mile": 4733, "location": {"lat": 36.1699, "lon": -115.1398}},
    {"city": "Albuquerque",  "county": "Bernalillo",  "state": "NM", "population": 564559,  "density_per_sq_mile": 3117, "location": {"lat": 35.0844, "lon": -106.6504}},
    {"city": "Tucson",       "county": "Pima",        "state": "AZ", "population": 542629,  "density_per_sq_mile": 2397, "location": {"lat": 32.2226, "lon": -110.9747}},
    {"city": "Fresno",       "county": "Fresno",      "state": "CA", "population": 542107,  "density_per_sq_mile": 4550, "location": {"lat": 36.7378, "lon": -119.7871}},
    {"city": "Sacramento",   "county": "Sacramento",  "state": "CA", "population": 513624,  "density_per_sq_mile": 5021, "location": {"lat": 38.5816, "lon": -121.4944}},
    {"city": "Kansas City",  "county": "Jackson",     "state": "MO", "population": 508090,  "density_per_sq_mile": 1476, "location": {"lat": 39.0997, "lon": -94.5786}},
    {"city": "Atlanta",      "county": "Fulton",      "state": "GA", "population": 498715,  "density_per_sq_mile": 3598, "location": {"lat": 33.7490, "lon": -84.3880}},
]

HAZMAT_DATA = [
    {"facility_name": "Gulf Coast Refinery",         "facility_type": "Oil Refinery",       "hazmat_class": ["flammable_liquid", "toxic"],        "risk_tier": "critical", "location": {"lat": 29.7200, "lon": -95.2100}},
    {"facility_name": "Phoenix Chemical Storage",     "facility_type": "Chemical Storage",   "hazmat_class": ["corrosive", "oxidizer"],            "risk_tier": "high",     "location": {"lat": 33.4200, "lon": -112.0500}},
    {"facility_name": "SA Petrochemical Plant",       "facility_type": "Petrochemical",      "hazmat_class": ["flammable_gas", "toxic"],           "risk_tier": "critical", "location": {"lat": 29.3900, "lon": -98.5200}},
    {"facility_name": "DFW Industrial Chemicals",    "facility_type": "Chemical Storage",   "hazmat_class": ["corrosive", "flammable_liquid"],    "risk_tier": "high",     "location": {"lat": 32.8000, "lon": -97.0000}},
    {"facility_name": "LA Harbor Fuel Terminal",      "facility_type": "Fuel Terminal",      "hazmat_class": ["flammable_liquid"],                 "risk_tier": "high",     "location": {"lat": 33.7300, "lon": -118.2600}},
    {"facility_name": "Chicago Rail Yard Hazmat",     "facility_type": "Rail Yard",          "hazmat_class": ["flammable_gas", "toxic", "explosive"],"risk_tier": "critical","location": {"lat": 41.8500, "lon": -87.6500}},
    {"facility_name": "Jacksonville Port Chemicals",  "facility_type": "Port Facility",      "hazmat_class": ["corrosive", "oxidizer"],            "risk_tier": "medium",   "location": {"lat": 30.3200, "lon": -81.6300}},
    {"facility_name": "Columbus Propane Depot",       "facility_type": "Gas Storage",        "hazmat_class": ["flammable_gas"],                    "risk_tier": "medium",   "location": {"lat": 39.9800, "lon": -83.0100}},
    {"facility_name": "Austin Semiconductor Fab",     "facility_type": "Manufacturing",      "hazmat_class": ["toxic", "corrosive"],               "risk_tier": "high",     "location": {"lat": 30.2500, "lon": -97.7600}},
    {"facility_name": "Memphis Rail Chemical Hub",    "facility_type": "Rail Yard",          "hazmat_class": ["flammable_liquid", "toxic"],        "risk_tier": "high",     "location": {"lat": 35.1300, "lon": -90.0700}},
    {"facility_name": "OKC Natural Gas Plant",        "facility_type": "Gas Processing",     "hazmat_class": ["flammable_gas"],                    "risk_tier": "high",     "location": {"lat": 35.4500, "lon": -97.5400}},
    {"facility_name": "Tulsa Pipeline Terminal",      "facility_type": "Pipeline Terminal",  "hazmat_class": ["flammable_liquid"],                 "risk_tier": "medium",   "location": {"lat": 36.1300, "lon": -96.0100}},
    {"facility_name": "New Orleans Port Hazmat",      "facility_type": "Port Facility",      "hazmat_class": ["corrosive", "flammable_liquid"],    "risk_tier": "critical", "location": {"lat": 29.9300, "lon": -90.0900}},
    {"facility_name": "Tampa Bay Chemical Terminal",  "facility_type": "Chemical Storage",   "hazmat_class": ["oxidizer", "toxic"],                "risk_tier": "high",     "location": {"lat": 27.9200, "lon": -82.4800}},
    {"facility_name": "Denver Chlorine Plant",        "facility_type": "Water Treatment",    "hazmat_class": ["toxic", "corrosive"],               "risk_tier": "medium",   "location": {"lat": 39.7200, "lon": -104.9700}},
    {"facility_name": "Portland Fuel Tank Farm",      "facility_type": "Fuel Terminal",      "hazmat_class": ["flammable_liquid"],                 "risk_tier": "medium",   "location": {"lat": 45.4900, "lon": -122.6900}},
    {"facility_name": "Las Vegas Propane Storage",    "facility_type": "Gas Storage",        "hazmat_class": ["flammable_gas"],                    "risk_tier": "low",      "location": {"lat": 36.1500, "lon": -115.1600}},
    {"facility_name": "Albuquerque Rail Depot",       "facility_type": "Rail Yard",          "hazmat_class": ["flammable_liquid", "corrosive"],   "risk_tier": "medium",   "location": {"lat": 35.0700, "lon": -106.6700}},
    {"facility_name": "Tucson Mining Chemicals",      "facility_type": "Mining Support",     "hazmat_class": ["corrosive", "oxidizer"],            "risk_tier": "high",     "location": {"lat": 32.2000, "lon": -110.9900}},
    {"facility_name": "Fresno Ag Chemical Storage",   "facility_type": "Agricultural",       "hazmat_class": ["toxic", "corrosive"],               "risk_tier": "medium",   "location": {"lat": 36.7200, "lon": -119.8000}},
    {"facility_name": "Sacramento Fuel Depot",        "facility_type": "Fuel Terminal",      "hazmat_class": ["flammable_liquid"],                 "risk_tier": "low",      "location": {"lat": 38.5600, "lon": -121.5100}},
    {"facility_name": "Kansas City Chem Plant",       "facility_type": "Chemical Storage",   "hazmat_class": ["toxic", "flammable_liquid"],       "risk_tier": "high",     "location": {"lat": 39.0800, "lon": -94.5900}},
    {"facility_name": "Atlanta Industrial Park",      "facility_type": "Manufacturing",      "hazmat_class": ["corrosive"],                        "risk_tier": "low",      "location": {"lat": 33.7300, "lon": -84.4000}},
    {"facility_name": "Baltimore Port Chemicals",     "facility_type": "Port Facility",      "hazmat_class": ["toxic", "oxidizer"],               "risk_tier": "high",     "location": {"lat": 39.2700, "lon": -76.6000}},
    {"facility_name": "Louisville Chemical Depot",    "facility_type": "Chemical Storage",   "hazmat_class": ["flammable_liquid", "corrosive"],   "risk_tier": "medium",   "location": {"lat": 38.2400, "lon": -85.7700}},
]

INCIDENT_DATA = [
    {"event_type": "wildfire",       "date": "2024-08-15", "severity": 8, "affected_radius_miles": 45, "casualties": 3,  "location": {"lat": 34.1000, "lon": -118.3000}},
    {"event_type": "chemical_spill", "date": "2023-11-02", "severity": 6, "affected_radius_miles": 5,  "casualties": 0,  "location": {"lat": 29.7500, "lon": -95.3500}},
    {"event_type": "tornado",        "date": "2024-04-27", "severity": 9, "affected_radius_miles": 20, "casualties": 12, "location": {"lat": 35.4700, "lon": -97.5200}},
    {"event_type": "explosion",      "date": "2023-06-18", "severity": 7, "affected_radius_miles": 3,  "casualties": 2,  "location": {"lat": 29.3800, "lon": -98.5100}},
    {"event_type": "flood",          "date": "2024-09-10", "severity": 7, "affected_radius_miles": 30, "casualties": 1,  "location": {"lat": 30.3300, "lon": -81.6600}},
    {"event_type": "wildfire",       "date": "2023-07-04", "severity": 9, "affected_radius_miles": 80, "casualties": 0,  "location": {"lat": 39.7500, "lon": -105.0000}},
    {"event_type": "chemical_spill", "date": "2024-01-22", "severity": 5, "affected_radius_miles": 2,  "casualties": 0,  "location": {"lat": 41.8700, "lon": -87.6400}},
    {"event_type": "tornado",        "date": "2023-05-20", "severity": 8, "affected_radius_miles": 15, "casualties": 5,  "location": {"lat": 36.1600, "lon": -95.9900}},
    {"event_type": "explosion",      "date": "2024-03-11", "severity": 6, "affected_radius_miles": 4,  "casualties": 1,  "location": {"lat": 29.9400, "lon": -90.0800}},
    {"event_type": "flood",          "date": "2023-08-29", "severity": 8, "affected_radius_miles": 50, "casualties": 4,  "location": {"lat": 29.9500, "lon": -90.0700}},
    {"event_type": "wildfire",       "date": "2024-10-01", "severity": 7, "affected_radius_miles": 35, "casualties": 0,  "location": {"lat": 45.5100, "lon": -122.6600}},
    {"event_type": "chemical_spill", "date": "2023-04-14", "severity": 4, "affected_radius_miles": 1,  "casualties": 0,  "location": {"lat": 36.1400, "lon": -96.0000}},
    {"event_type": "tornado",        "date": "2024-06-03", "severity": 7, "affected_radius_miles": 10, "casualties": 2,  "location": {"lat": 39.1000, "lon": -94.5800}},
    {"event_type": "explosion",      "date": "2023-09-25", "severity": 8, "affected_radius_miles": 6,  "casualties": 3,  "location": {"lat": 29.7300, "lon": -95.2200}},
    {"event_type": "flood",          "date": "2024-07-18", "severity": 6, "affected_radius_miles": 20, "casualties": 0,  "location": {"lat": 27.9400, "lon": -82.4600}},
    {"event_type": "wildfire",       "date": "2023-10-12", "severity": 8, "affected_radius_miles": 60, "casualties": 1,  "location": {"lat": 36.7400, "lon": -119.7900}},
    {"event_type": "chemical_spill", "date": "2024-02-08", "severity": 7, "affected_radius_miles": 8,  "casualties": 0,  "location": {"lat": 33.4300, "lon": -112.0600}},
    {"event_type": "tornado",        "date": "2023-03-31", "severity": 6, "affected_radius_miles": 8,  "casualties": 0,  "location": {"lat": 35.1400, "lon": -90.0600}},
    {"event_type": "explosion",      "date": "2024-05-19", "severity": 5, "affected_radius_miles": 2,  "casualties": 0,  "location": {"lat": 32.7900, "lon": -96.8000}},
    {"event_type": "flood",          "date": "2023-12-05", "severity": 5, "affected_radius_miles": 15, "casualties": 0,  "location": {"lat": 38.5700, "lon": -121.5000}},
    {"event_type": "wildfire",       "date": "2024-08-22", "severity": 6, "affected_radius_miles": 25, "casualties": 0,  "location": {"lat": 35.0900, "lon": -106.6600}},
    {"event_type": "chemical_spill", "date": "2023-07-30", "severity": 8, "affected_radius_miles": 10, "casualties": 2,  "location": {"lat": 39.2800, "lon": -76.6100}},
    {"event_type": "tornado",        "date": "2024-04-15", "severity": 9, "affected_radius_miles": 25, "casualties": 8,  "location": {"lat": 33.7600, "lon": -84.3900}},
    {"event_type": "explosion",      "date": "2023-11-28", "severity": 9, "affected_radius_miles": 10, "casualties": 5,  "location": {"lat": 38.2600, "lon": -85.7600}},
    {"event_type": "flood",          "date": "2024-06-22", "severity": 7, "affected_radius_miles": 35, "casualties": 2,  "location": {"lat": 39.9700, "lon": -82.9900}},
]


def create_indexes():
    for name, body in MAPPINGS.items():
        if es.indices.exists(index=name):
            print(f"  ⚠️  Index '{name}' already exists — skipping creation.")
        else:
            es.indices.create(index=name, body=body)
            print(f"  ✅ Created index '{name}'")


def seed_index(index_name, records):
    success = 0
    for i, record in enumerate(records):
        try:
            es.index(index=index_name, id=i + 1, body=record)
            success += 1
        except Exception as e:
            print(f"  ❌ Failed to insert record {i+1}: {e}")
    print(f"  ✅ Seeded {success}/{len(records)} records into '{index_name}'")


if __name__ == "__main__":
    print("\n🛡️  AeroShield — Elasticsearch Setup\n")

    print("📡 Testing connection...")
    info = es.info()
    print(f"  ✅ Connected to cluster: {info['cluster_name']}\n")

    print("📁 Creating indexes...")
    create_indexes()

    print("\n📦 Seeding data...")
    seed_index("population_density",    POPULATION_DATA)
    seed_index("hazmat_infrastructure", HAZMAT_DATA)
    seed_index("incident_history",      INCIDENT_DATA)

    print("\n🎉 Setup complete! AeroShield indexes are ready.\n")
