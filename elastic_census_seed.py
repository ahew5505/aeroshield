"""
AeroShield - Census Tract Population Seeder
Pulls 2020 Census tract-level population data for all 50 states
and loads it into Elasticsearch. Supports resume on interruption.
"""
import os
import json
import time
import urllib.request
import urllib.parse
from elasticsearch import Elasticsearch, helpers

ELASTIC_URL = os.environ.get("ELASTIC_URL", "https://my-elasticsearch-project-da6e0d.es.us-central1.gcp.elastic.cloud:443")
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY", "")

es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

# All 50 states + DC FIPS codes
STATES = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
    "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
    "11": "District of Columbia", "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa",
    "20": "Kansas", "21": "Kentucky", "22": "Louisiana", "23": "Maine",
    "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska",
    "32": "Nevada", "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico",
    "36": "New York", "37": "North Carolina", "38": "North Dakota", "39": "Ohio",
    "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island",
    "45": "South Carolina", "46": "South Dakota", "47": "Tennessee", "48": "Texas",
    "49": "Utah", "50": "Vermont", "51": "Virginia", "53": "Washington",
    "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming",
}

INDEX_NAME = "population_density"

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "tract_id":            {"type": "keyword"},
            "state_fips":          {"type": "keyword"},
            "county_fips":         {"type": "keyword"},
            "tract_fips":          {"type": "keyword"},
            "name":                {"type": "text"},
            "state":               {"type": "keyword"},
            "county":              {"type": "keyword"},
            "population":          {"type": "integer"},
            "location":            {"type": "geo_point"},
        }
    }
}

PROGRESS_FILE = "census_seed_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed_states": [], "total_loaded": 0}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)

def fetch_url(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AeroShield/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt < retries - 1:
                print(f"    ⚠️  Retry {attempt+1}/{retries}: {e}")
                time.sleep(delay)
            else:
                raise

def get_tract_population(state_fips):
    """Fetch all census tracts and populations for a state."""
    url = (
        f"https://api.census.gov/data/2020/dec/pl"
        f"?get=P1_001N,NAME&for=tract:*&in=state:{state_fips}&in=county:*&key=7694ce8c4ca7129a20a4db1ad9512a014e500d4c"
    )
    data = fetch_url(url)
    # First row is headers: [P1_001N, NAME, state, county, tract]
    headers = data[0]
    rows = data[1:]
    tracts = []
    for row in rows:
        record = dict(zip(headers, row))
        tracts.append({
            "population":   int(record.get("P1_001N", 0)),
            "name":         record.get("NAME", ""),
            "state_fips":   record.get("state", ""),
            "county_fips":  record.get("county", ""),
            "tract_fips":   record.get("tract", ""),
        })
    return tracts

def get_tract_centroid(state_fips, county_fips, tract_fips, retries=3):
    """Get lat/lon centroid for a census tract via TIGERweb REST API."""
    url = (
        f"https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2020/MapServer/8/query"
        f"?where=STATE%3D%27{state_fips}%27+AND+COUNTY%3D%27{county_fips}%27+AND+TRACT%3D%27{tract_fips}%27"
        f"&outFields=CENTLAT,CENTLON&f=json"
    )
    for attempt in range(retries):
        try:
            data = fetch_url(url)
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                lat = float(attrs.get("CENTLAT", 0))
                lon = float(attrs.get("CENTLON", 0))
                if lat != 0 and lon != 0:
                    return lat, lon
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
    return None, None

def bulk_index(documents):
    """Bulk index documents into Elasticsearch."""
    actions = [
        {
            "_index": INDEX_NAME,
            "_id": doc["tract_id"],
            "_source": doc,
        }
        for doc in documents
    ]
    success, errors = helpers.bulk(es, actions, raise_on_error=False)
    return success, errors

def seed_state(state_fips, state_name, progress):
    print(f"\n📍 {state_name} ({state_fips})")

    # Fetch tract population data
    try:
        tracts = get_tract_population(state_fips)
        print(f"   Found {len(tracts)} tracts")
    except Exception as e:
        print(f"   ❌ Failed to fetch tracts: {e}")
        return 0

    documents = []
    skipped = 0

    for i, tract in enumerate(tracts):
        county_fips = tract["county_fips"]
        tract_fips  = tract["tract_fips"]
        tract_id    = f"{state_fips}{county_fips}{tract_fips}"

        # Skip zero population tracts
        if tract["population"] == 0:
            skipped += 1
            continue

        # Get centroid
        lat, lon = get_tract_centroid(state_fips, county_fips, tract_fips)
        if lat is None:
            skipped += 1
            continue

        documents.append({
            "tract_id":    tract_id,
            "state_fips":  state_fips,
            "county_fips": county_fips,
            "tract_fips":  tract_fips,
            "name":        tract["name"],
            "state":       state_name,
            "population":  tract["population"],
            "location":    {"lat": lat, "lon": lon},
        })

        # Bulk index every 100 records
        if len(documents) >= 100:
            success, _ = bulk_index(documents)
            progress["total_loaded"] += success
            documents = []

        # Progress update every 50 tracts
        if (i + 1) % 50 == 0:
            print(f"   ... {i+1}/{len(tracts)} tracts processed, {progress['total_loaded']} total loaded")

        # Small delay to be respectful to Census API
        time.sleep(0.05)

    # Index remaining
    if documents:
        success, _ = bulk_index(documents)
        progress["total_loaded"] += success

    print(f"   ✅ Done — {len(tracts) - skipped} tracts loaded, {skipped} skipped")
    return len(tracts) - skipped


if __name__ == "__main__":
    print("\n🛡️  AeroShield — Census Tract Population Seeder")
    print("   Coverage: All 50 states + DC")
    print("   Source: 2020 US Census via Census API + TIGERweb\n")

    # Create index if needed
    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
        print(f"✅ Created index '{INDEX_NAME}'\n")
    else:
        print(f"ℹ️  Index '{INDEX_NAME}' already exists — appending data\n")

    # Load progress for resume support
    progress = load_progress()
    completed = set(progress["completed_states"])
    print(f"📊 Previously completed: {len(completed)} states, {progress['total_loaded']} tracts loaded")

    for state_fips, state_name in STATES.items():
        if state_fips in completed:
            print(f"   ⏭️  Skipping {state_name} (already completed)")
            continue

        count = seed_state(state_fips, state_name, progress)
        progress["completed_states"].append(state_fips)
        save_progress(progress)
        print(f"   💾 Progress saved — {progress['total_loaded']} total tracts in Elasticsearch")

        # Pause between states
        time.sleep(1)

    print(f"\n🎉 Seeding complete! {progress['total_loaded']} census tracts loaded into Elasticsearch.")
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
