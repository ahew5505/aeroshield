# ruff: noqa
# Copyright 2026 AeroShield Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0

import os
import math
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.cloud import secretmanager
from elasticsearch import Elasticsearch

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

def _get_secret(secret_id: str) -> str:
    """Fetch a secret value from GCP Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Load credentials from Secret Manager, fall back to env vars for local dev
ELASTIC_URL = os.environ.get("ELASTIC_URL") or _get_secret("elastic-url")
ELASTIC_API_KEY = os.environ.get("ELASTIC_API_KEY") or _get_secret("elastic-api-key")

# Elasticsearch client
es = Elasticsearch(ELASTIC_URL, api_key=ELASTIC_API_KEY)

def _bounding_box(lat: float, lon: float, radius_miles: float):
    """Return a geo bounding box dict for an Elasticsearch filter."""
    deg_lat = radius_miles / 69.0
    deg_lon = radius_miles / (69.0 * math.cos(math.radians(lat)))
    return {
        "top_left":     {"lat": lat + deg_lat, "lon": lon - deg_lon},
        "bottom_right": {"lat": lat - deg_lat, "lon": lon + deg_lon},
    }

def search_population_data(lat: float, lon: float, radius_miles: float = 50.0) -> dict:
    """Search population density data near a given location.

    Args:
        lat: Latitude of the incident location.
        lon: Longitude of the incident location.
        radius_miles: Search radius in miles (default 50).

    Returns:
        Dictionary with total population, record count, and top populated areas nearby.
    """
    try:
        box = _bounding_box(lat, lon, radius_miles)
        resp = es.search(index="population_density", body={
            "size": 10,
            "query": {"geo_bounding_box": {"location": box}},
            "sort": [{"population": {"order": "desc"}}],
        })
        hits = resp["hits"]["hits"]
        total_pop = sum(h["_source"].get("population", 0) for h in hits)
        areas = [
            {
                "city": h["_source"].get("city"),
                "state": h["_source"].get("state"),
                "population": h["_source"].get("population"),
                "density_per_sq_mile": h["_source"].get("density_per_sq_mile"),
            }
            for h in hits
        ]
        return {"total_population_nearby": total_pop, "areas": areas, "records_found": len(hits)}
    except Exception as e:
        return {"error": str(e), "total_population_nearby": 0, "areas": []}


def search_hazmat_facilities(lat: float, lon: float, radius_miles: float = 30.0) -> dict:
    """Search for hazardous material facilities near a given location.

    Args:
        lat: Latitude of the incident location.
        lon: Longitude of the incident location.
        radius_miles: Search radius in miles (default 30).

    Returns:
        Dictionary with facility list, count, and highest risk tier found.
    """
    try:
        box = _bounding_box(lat, lon, radius_miles)
        resp = es.search(index="hazmat_infrastructure", body={
            "size": 10,
            "query": {"geo_bounding_box": {"location": box}},
        })
        hits = resp["hits"]["hits"]
        tier_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        facilities = [
            {
                "name": h["_source"].get("facility_name"),
                "type": h["_source"].get("facility_type"),
                "hazmat_class": h["_source"].get("hazmat_class", []),
                "risk_tier": h["_source"].get("risk_tier"),
            }
            for h in hits
        ]
        highest = max(facilities, key=lambda f: tier_rank.get(f["risk_tier"], 0), default=None)
        return {
            "facility_count": len(facilities),
            "facilities": facilities,
            "highest_risk_tier": highest["risk_tier"] if highest else "none",
        }
    except Exception as e:
        return {"error": str(e), "facility_count": 0, "facilities": [], "highest_risk_tier": "none"}


def search_incident_history(event_type: str, lat: float, lon: float, radius_miles: float = 100.0) -> dict:
    """Search historical incident records for similar events near a location.

    Args:
        event_type: Type of incident (wildfire, chemical_spill, explosion, tornado, flood, earthquake, other).
        lat: Latitude of the incident location.
        lon: Longitude of the incident location.
        radius_miles: Search radius in miles (default 100).

    Returns:
        Dictionary with historical incidents, average severity, and max affected radius.
    """
    try:
        box = _bounding_box(lat, lon, radius_miles)
        resp = es.search(index="incident_history", body={
            "size": 10,
            "query": {
                "bool": {
                    "must": [{"match": {"event_type": event_type}}],
                    "filter": [{"geo_bounding_box": {"location": box}}],
                }
            },
            "sort": [{"date": {"order": "desc"}}],
        })
        hits = resp["hits"]["hits"]
        severities = [h["_source"].get("severity", 0) for h in hits]
        radii = [h["_source"].get("affected_radius_miles", 0) for h in hits]
        incidents = [
            {
                "date": h["_source"].get("date"),
                "severity": h["_source"].get("severity"),
                "affected_radius_miles": h["_source"].get("affected_radius_miles"),
                "casualties": h["_source"].get("casualties"),
            }
            for h in hits
        ]
        return {
            "historical_count": len(hits),
            "average_severity": round(sum(severities) / len(severities), 1) if severities else 0,
            "max_affected_radius_miles": max(radii) if radii else 0,
            "incidents": incidents,
        }
    except Exception as e:
        return {"error": str(e), "historical_count": 0, "incidents": []}



def geocode_location(location_query: str) -> dict:
    """Convert a place name, address, or landmark to coordinates using OpenStreetMap Nominatim.

    Args:
        location_query: Any location string — city, address, landmark, school, hospital, company, etc.

    Returns:
        Dictionary with lat, lon, display_name, and city/state if available.
    """
    import urllib.request
    import urllib.parse
    import json
    try:
        query = urllib.parse.urlencode({"q": location_query, "format": "json", "limit": 1, "addressdetails": 1})
        url = f"https://nominatim.openstreetmap.org/search?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": "AeroShield/1.0 (emergency-risk-assessment)"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            results = json.loads(resp.read())
        if not results:
            return {"error": f"Could not find location: {location_query}"}
        r = results[0]
        addr = r.get("address", {})
        return {
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "display_name": r.get("display_name"),
            "city": addr.get("city") or addr.get("town") or addr.get("village"),
            "state": addr.get("state"),
            "country": addr.get("country"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_weather_conditions(lat: float, lon: float) -> dict:
    """Fetch live meteorological conditions for a given location using Open-Meteo.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.

    Returns:
        Dictionary with wind speed, wind direction, temperature, precipitation, and a plain-English summary.
    """
    import urllib.request
    import json
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,precipitation,wind_speed_10m,wind_direction_10m"
            f"&wind_speed_unit=mph&temperature_unit=fahrenheit&forecast_days=1"
        )
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        current = data["current"]
        wind_deg = current["wind_direction_10m"]
        dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
        cardinal = dirs[round(wind_deg / 22.5) % 16]
        wind_mph = current["wind_speed_10m"]
        temp_f = current["temperature_2m"]
        precip = current["precipitation"]
        summary = (
            f"Current conditions: {temp_f}°F, wind {wind_mph} mph from the {cardinal} "
            f"({wind_deg}°), precipitation {precip} mm."
        )
        return {
            "wind_speed_mph": wind_mph,
            "wind_direction_deg": wind_deg,
            "wind_cardinal": cardinal,
            "temperature_f": temp_f,
            "precipitation_mm": precip,
            "summary": summary,
        }
    except Exception as e:
        return {"error": str(e), "wind_speed_mph": 0, "wind_direction_deg": 0, "summary": "Weather data unavailable."}


def calculate_plume_model(
    lat: float,
    lon: float,
    event_type: str,
    wind_speed_mph: float,
    wind_direction_deg: float,
    severity: int,
) -> dict:
    """Calculate a wind-driven hazard plume model and return GeoJSON polygon + visualization link.

    Args:
        lat: Latitude of the incident origin.
        lon: Longitude of the incident origin.
        event_type: Type of incident (wildfire, chemical_spill, explosion, tornado, flood, other).
        wind_speed_mph: Current wind speed in mph.
        wind_direction_deg: Wind direction in degrees (direction wind is coming FROM).
        severity: Incident severity 1-10.

    Returns:
        Dictionary with GeoJSON polygon, geojson.io visualization link, and plain-English plume summary.
    """
    import math
    import json
    import urllib.parse

    # Plume travels OPPOSITE to wind origin direction
    travel_deg = (wind_direction_deg + 180) % 360
    travel_rad = math.radians(travel_deg)

    # Scale plume length by wind speed and severity
    base_length_miles = 2 + (wind_speed_mph / 10) * (severity / 5)
    plume_length = min(base_length_miles, 40)  # cap at 40 miles

    # Cone half-angle widens with lower wind speed (more diffuse at low speed)
    if wind_speed_mph < 10:
        half_angle_deg = 45
    elif wind_speed_mph < 20:
        half_angle_deg = 30
    else:
        half_angle_deg = 20

    # Upwind blast radius for explosions
    blast_radius_miles = (severity / 10) * 2 if event_type == "explosion" else 0

    # Degrees per mile (approximate)
    deg_per_mile_lat = 1 / 69.0
    deg_per_mile_lon = 1 / (69.0 * math.cos(math.radians(lat)))

    def point_at(origin_lat, origin_lon, bearing_deg, distance_miles):
        b = math.radians(bearing_deg)
        return [
            origin_lon + math.sin(b) * distance_miles * deg_per_mile_lon,
            origin_lat + math.cos(b) * distance_miles * deg_per_mile_lat,
        ]

    # Build cone polygon: origin -> left edge -> tip -> right edge -> origin
    left_bearing  = (travel_deg - half_angle_deg) % 360
    right_bearing = (travel_deg + half_angle_deg) % 360

    origin_point  = [lon, lat]
    left_mid      = point_at(lat, lon, left_bearing,  plume_length * 0.5)
    left_tip      = point_at(lat, lon, left_bearing,  plume_length)
    center_tip    = point_at(lat, lon, travel_deg,    plume_length)
    right_tip     = point_at(lat, lon, right_bearing, plume_length)
    right_mid     = point_at(lat, lon, right_bearing, plume_length * 0.5)

    cone_coords = [origin_point, left_mid, left_tip, center_tip, right_tip, right_mid, origin_point]

    # Color by event type
    colors = {
        "wildfire":       "#FF4500",
        "chemical_spill": "#9400D3",
        "explosion":      "#FF8C00",
        "tornado":        "#1E90FF",
        "flood":          "#00BFFF",
    }
    color = colors.get(event_type, "#FF0000")

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [cone_coords]},
            "properties": {
                "name": f"{event_type.replace('_', ' ').title()} Plume",
                "event_type": event_type,
                "plume_length_miles": round(plume_length, 1),
                "wind_speed_mph": wind_speed_mph,
                "wind_direction_deg": wind_direction_deg,
                "severity": severity,
                "fill": color,
                "fill-opacity": 0.4,
                "stroke": color,
            },
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": origin_point},
            "properties": {"name": "Incident Origin", "marker-color": "#FF0000", "marker-size": "large"},
        },
    ]

    # Add blast radius circle for explosions (approximate with polygon)
    if blast_radius_miles > 0:
        blast_coords = [
            point_at(lat, lon, angle, blast_radius_miles)
            for angle in range(0, 361, 10)
        ]
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [blast_coords]},
            "properties": {"name": "Blast Radius", "fill": "#FF0000", "fill-opacity": 0.2, "stroke": "#FF0000"},
        })

    geojson = {"type": "FeatureCollection", "features": features}
    geojson_str = json.dumps(geojson, separators=(",", ":"))
    encoded = urllib.parse.quote(geojson_str, safe="")
    viz_link = f"https://geojson.io/#data=data:application/json,{encoded}"

    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    cardinal = dirs[round(wind_direction_deg / 22.5) % 16]
    plume_cardinal = dirs[round(travel_deg / 22.5) % 16]

    summary = (
        f"Plume is projected to travel {plume_cardinal} driven by {wind_speed_mph} mph winds from the {cardinal}. "
        f"Estimated plume extent: {round(plume_length, 1)} miles. "
        f"Cone spread angle: ±{half_angle_deg}°."
    )

    return {
        "plume_length_miles": round(plume_length, 1),
        "plume_direction": plume_cardinal,
        "wind_from": cardinal,
        "half_angle_deg": half_angle_deg,
        "geojson": geojson,
        "visualization_link": viz_link,
        "summary": summary,
    }


def calculate_risk_score(
    event_type: str,
    severity: int,
    population_count: int,
    hazmat_facility_count: int,
    highest_hazmat_tier: str,
    wind_speed_mph: float = 0.0,
) -> dict:
    """Calculate an AeroShield risk score and recommended evacuation radius.

    Args:
        event_type: Type of incident (wildfire, chemical_spill, explosion, tornado, flood, earthquake, other).
        severity: Incident severity on a scale of 1-10.
        population_count: Estimated population in the affected area.
        hazmat_facility_count: Number of hazmat facilities nearby.
        highest_hazmat_tier: Highest risk tier among nearby facilities (none/low/medium/high/critical).
        wind_speed_mph: Current wind speed in mph (relevant for airborne hazards).

    Returns:
        Dictionary with risk score, risk tier, evacuation radius, and plain-English summary.
    """
    # Population exposure score (0-40)
    if population_count > 500000:
        pop_score = 40
    elif population_count > 100000:
        pop_score = 30
    elif population_count > 50000:
        pop_score = 20
    elif population_count > 10000:
        pop_score = 12
    else:
        pop_score = 5

    # Hazmat proximity score (0-35)
    tier_scores = {"critical": 35, "high": 25, "medium": 15, "low": 8, "none": 0}
    hazmat_score = tier_scores.get(highest_hazmat_tier, 0)
    if hazmat_facility_count > 3:
        hazmat_score = min(35, hazmat_score + 5)

    # Event severity score (0-25)
    severity_score = round((severity / 10) * 25)

    # Wind modifier for airborne events
    wind_bonus = 0
    if event_type in ("wildfire", "chemical_spill") and wind_speed_mph > 20:
        wind_bonus = min(10, round((wind_speed_mph - 20) / 5))

    total_score = min(100, pop_score + hazmat_score + severity_score + wind_bonus)

    # Tier thresholds
    if total_score >= 80:
        risk_tier = "CRITICAL"
        evac_radius = 25
    elif total_score >= 56:
        risk_tier = "HIGH"
        evac_radius = 15
    elif total_score >= 31:
        risk_tier = "MODERATE"
        evac_radius = 7
    else:
        risk_tier = "LOW"
        evac_radius = 2

    # Adjust radius for wind-driven events
    if wind_speed_mph > 20 and event_type in ("wildfire", "chemical_spill"):
        evac_radius = round(evac_radius * 1.4)

    summary = (
        f"AeroShield has assessed this {event_type.replace('_', ' ')} as {risk_tier} risk "
        f"(score: {total_score}/100). "
        f"An estimated {population_count:,} people are within the affected area, "
        f"with {hazmat_facility_count} hazmat facilit{'y' if hazmat_facility_count == 1 else 'ies'} nearby. "
        f"Recommended evacuation radius: {evac_radius} miles. "
        f"This assessment is a decision-support tool for emergency managers and does not constitute an official emergency order."
    )

    return {
        "risk_score": total_score,
        "risk_tier": risk_tier,
        "recommended_evacuation_radius_miles": evac_radius,
        "score_breakdown": {
            "population_exposure": pop_score,
            "hazmat_proximity": hazmat_score,
            "event_severity": severity_score,
            "wind_modifier": wind_bonus,
        },
        "assessment_summary": summary,
    }


SYSTEM_PROMPT = """You are AeroShield, a professional environmental and population risk assessment system designed to support emergency managers, first responders, and public safety officials.

Your mission is to assess risk from hazard events including wildfires, chemical spills, explosions, tornadoes, floods, earthquakes, and other incidents.

## Workflow
When a user reports an incident, follow these steps in order:
1. Collect the event type, location (any format — city, address, landmark, school, hospital, etc.), and severity (1-10).
2. ALWAYS call `geocode_location` first to resolve the location to precise coordinates — even if the user provides a city name. Never skip this step.
3. Call `search_population_data` with the location coordinates to get nearby population figures.
4. Call `search_hazmat_facilities` to identify nearby hazardous material facilities.
5. Call `search_incident_history` to provide historical context for similar events. Explicitly report: how many similar events occurred nearby, the date range, average severity, maximum affected radius, and any casualties. If no history exists, state that clearly.
6. Call `get_weather_conditions` with the same coordinates — ALWAYS do this automatically, never ask the user for weather or wind data.
7. For wildfire, chemical_spill, and explosion events, call `calculate_plume_model` using the coordinates, event type, and wind data from `get_weather_conditions`.

8. Call `calculate_risk_score` with all gathered data to produce the official risk assessment.
6. Present a structured report (see format below). For wildfire, chemical_spill, and explosion events, always include the raw GeoJSON from `calculate_plume_model` in a ```json code block at the end of the report so users can copy and paste it into https://geojson.io for visualization.

## Report Format
Always present results in this structure:

---
🛡️ AEROSHIELD RISK ASSESSMENT
Event: [type] | Location: [city, state] | Severity: [X/10]

🔴/🟠/🟡/🟢 RISK TIER: [CRITICAL/HIGH/MODERATE/LOW] (Score: XX/100)

👥 Population Exposure: [X,XXX,XXX people in affected area]
☣️ Hazmat Facilities: [X facilities within radius, highest tier: Y]
📍 Recommended Evacuation Radius: [X miles]
🌬️ Plume Projection: [plume direction, length, spread angle]
🚗 Evacuation Routes: [2-3 specific cardinal directions to evacuate toward, explicitly avoiding the plume direction and any nearby hazmat facilities. Example: "Move NORTH or EAST — avoid southward routes due to plume travel and Gulf Coast Refinery to the southwest"]
🗺️ GeoJSON: Copy the raw geojson from the plume model output and paste it at https://geojson.io to visualize the plume on a map.

📜 Historical Context: [X similar events within 100 miles since [date]. Average severity: X. Max affected radius: X miles. Total casualties recorded: X. OR "No historical incidents of this type found in the area."]

📋 Summary:
[Plain English 2-3 sentence summary]

⚠️ Disclaimer: This assessment is a decision-support tool for trained emergency personnel. It does not constitute an official emergency order or government directive.
---

## Guidelines
- Always use tools before presenting any risk figures — never estimate without data.
- If coordinates are not provided, infer approximate lat/lon from the city and state yourself — never ask the user for coordinates or weather data. Both are resolved automatically via tools.
- Be precise and professional. Avoid speculation beyond available data.
- If Elasticsearch returns no data, state that clearly and note the assessment is based on limited information.
- Never tell users to evacuate directly — frame everything as recommendations for emergency managers to act upon.
- Always include evacuation route guidance based on plume direction and hazmat facility locations. Recommend 2-3 specific cardinal or intercardinal directions (N, NE, E, etc.) that move people away from the plume and hazmat facilities. Explicitly name which directions to avoid and why.
"""

root_agent = Agent(
    name="app",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=SYSTEM_PROMPT,
    tools=[
        calculate_plume_model,

        geocode_location,

        get_weather_conditions,
        search_population_data,
        search_hazmat_facilities,
        search_incident_history,
        calculate_risk_score,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)