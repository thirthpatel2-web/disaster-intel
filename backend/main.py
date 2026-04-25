from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import random
import math
import json
from datetime import datetime, timedelta
import os
import asyncio

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except:
    GROQ_AVAILABLE = False

app = FastAPI(title="IRIS Disaster Intelligence System v4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Groq Client ─────────────────────────────────────────────────────────────
def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY", "")
    if api_key and GROQ_AVAILABLE:
        return Groq(api_key=api_key)
    return None

# ─── Cities Database ─────────────────────────────────────────────────────────
CITIES = {
    "Mumbai":        {"lat":19.0760,"lng":72.8777,"state":"Maharashtra",  "pop":20667656,"elev":14,  "coastal":True, "river":True, "forest":False,"zone":"III","annual_rain":2200},
    "Delhi":         {"lat":28.6139,"lng":77.2090,"state":"Delhi",        "pop":32941000,"elev":216, "coastal":False,"river":True, "forest":False,"zone":"IV", "annual_rain":650},
    "Chennai":       {"lat":13.0827,"lng":80.2707,"state":"Tamil Nadu",   "pop":10971108,"elev":6,   "coastal":True, "river":True, "forest":False,"zone":"III","annual_rain":1400},
    "Kolkata":       {"lat":22.5726,"lng":88.3639,"state":"West Bengal",  "pop":14850000,"elev":9,   "coastal":False,"river":True, "forest":False,"zone":"III","annual_rain":1600},
    "Bangalore":     {"lat":12.9716,"lng":77.5946,"state":"Karnataka",   "pop":13608684,"elev":920, "coastal":False,"river":False,"forest":True, "zone":"II", "annual_rain":970},
    "Hyderabad":     {"lat":17.3850,"lng":78.4867,"state":"Telangana",   "pop":10534418,"elev":542, "coastal":False,"river":True, "forest":False,"zone":"II", "annual_rain":800},
    "Pune":          {"lat":18.5204,"lng":73.8567,"state":"Maharashtra",  "pop":7276000, "elev":560, "coastal":False,"river":True, "forest":True, "zone":"III","annual_rain":700},
    "Ahmedabad":     {"lat":23.0225,"lng":72.5714,"state":"Gujarat",     "pop":8253226, "elev":53,  "coastal":False,"river":True, "forest":False,"zone":"III","annual_rain":780},
    "Jaipur":        {"lat":26.9124,"lng":75.7873,"state":"Rajasthan",   "pop":3930570, "elev":431, "coastal":False,"river":False,"forest":False,"zone":"II", "annual_rain":650},
    "Surat":         {"lat":21.1702,"lng":72.8311,"state":"Gujarat",     "pop":7784276, "elev":13,  "coastal":True, "river":True, "forest":False,"zone":"III","annual_rain":1200},
    "Wayanad":       {"lat":11.6854,"lng":76.1320,"state":"Kerala",      "pop":825000,  "elev":900, "coastal":False,"river":True, "forest":True, "zone":"III","annual_rain":2500},
    "Uttarakhand":   {"lat":30.0668,"lng":79.0193,"state":"Uttarakhand", "pop":11250858,"elev":1500,"coastal":False,"river":True, "forest":True, "zone":"IV", "annual_rain":1500},
    "Bhubaneswar":   {"lat":20.2961,"lng":85.8245,"state":"Odisha",      "pop":997237,  "elev":45,  "coastal":True, "river":True, "forest":True, "zone":"III","annual_rain":1500},
    "Guwahati":      {"lat":26.1445,"lng":91.7362,"state":"Assam",       "pop":1165874, "elev":55,  "coastal":False,"river":True, "forest":True, "zone":"V",  "annual_rain":1600},
    "Patna":         {"lat":25.5941,"lng":85.1376,"state":"Bihar",       "pop":2049156, "elev":53,  "coastal":False,"river":True, "forest":False,"zone":"IV", "annual_rain":1100},
    "Kochi":         {"lat":9.9312, "lng":76.2673,"state":"Kerala",      "pop":677381,  "elev":0,   "coastal":True, "river":True, "forest":True, "zone":"III","annual_rain":3000},
    "Visakhapatnam": {"lat":17.6868,"lng":83.2185,"state":"Andhra Pradesh","pop":2035922,"elev":45, "coastal":True, "river":False,"forest":True, "zone":"II", "annual_rain":1000},
    "Nagpur":        {"lat":21.1458,"lng":79.0882,"state":"Maharashtra",  "pop":2875000, "elev":310, "coastal":False,"river":True, "forest":True, "zone":"II", "annual_rain":1100},
    "Indore":        {"lat":22.7196,"lng":75.8577,"state":"Madhya Pradesh","pop":3276697,"elev":553, "coastal":False,"river":True, "forest":False,"zone":"II", "annual_rain":900},
    "Shimla":        {"lat":31.1048,"lng":77.1734,"state":"Himachal Pradesh","pop":169578,"elev":2206,"coastal":False,"river":True,"forest":True, "zone":"IV", "annual_rain":1575},
    "Srinagar":      {"lat":34.0837,"lng":74.7973,"state":"J&K",         "pop":1250000, "elev":1585,"coastal":False,"river":True, "forest":True, "zone":"V",  "annual_rain":650},
    "Imphal":        {"lat":24.8170,"lng":93.9368,"state":"Manipur",     "pop":414288,  "elev":786, "coastal":False,"river":True, "forest":True, "zone":"V",  "annual_rain":1470},
    "Dehradun":      {"lat":30.3165,"lng":78.0322,"state":"Uttarakhand", "pop":803983,  "elev":640, "coastal":False,"river":True, "forest":True, "zone":"IV", "annual_rain":2073},
    "Raipur":        {"lat":21.2514,"lng":81.6296,"state":"Chhattisgarh","pop":1010087, "elev":289, "coastal":False,"river":True, "forest":True, "zone":"II", "annual_rain":1300},
    "Thiruvananthapuram":{"lat":8.5241,"lng":76.9366,"state":"Kerala",   "pop":957730,  "elev":16,  "coastal":True, "river":True, "forest":True, "zone":"III","annual_rain":1700},
}

# ─── Models ───────────────────────────────────────────────────────────────────
class RiskRequest(BaseModel):
    city: str
    rainfall: float = 50
    temperature: float = 30
    humidity: float = 60
    wind_speed: float = 20
    river_level: float = 40
    soil_moisture: float = 50
    seismic_activity: float = 0
    air_quality_index: float = 100
    visibility_km: float = 10
    storm_surge: float = 0

class SOSRequest(BaseModel):
    message: str
    source: str = "Social Media"
    language: str = "en"

class ChatRequest(BaseModel):
    message: str
    city: Optional[str] = None
    context: Optional[Dict] = None
    history: Optional[List[Dict]] = None
    mode: str = "general"  # general, emergency, technical, briefing

class ResourceRequest(BaseModel):
    city: str
    disaster_type: str
    severity: float

class EarlyWarningRequest(BaseModel):
    city: str
    hours_ahead: int = 72

class EvacuationRequest(BaseModel):
    city: str
    disaster_type: str
    severity: float
    population_affected: int = 10000

class ImpactRequest(BaseModel):
    city: str
    disaster_type: str
    magnitude: float
    duration_hours: int = 24

class MultiCityRequest(BaseModel):
    cities: List[str]

class NewsRequest(BaseModel):
    city: Optional[str] = None
    disaster_type: Optional[str] = None

# ─── Risk Engine ──────────────────────────────────────────────────────────────
def compute_risks(city_data: dict, params: RiskRequest) -> dict:
    city = CITIES.get(params.city, {})
    elev = city.get("elev", 100)
    coastal = city.get("coastal", False)
    river = city.get("river", False)
    forest = city.get("forest", False)
    zone = city.get("zone", "II")
    seismic_base = {"II":0,"III":5,"IV":15,"V":25}.get(zone, 5)

    flood = min(100, (
        params.rainfall * 0.35 +
        params.humidity * 0.18 +
        params.river_level * 0.28 +
        params.soil_moisture * 0.12 +
        (20 if coastal else 0) +
        (15 if river else 0) +
        max(0, (60 - elev) * 0.15) +
        params.storm_surge * 0.4
    ))
    fire = min(100, (
        max(0, params.temperature - 25) * 2.8 +
        max(0, 70 - params.humidity) * 0.9 +
        params.wind_speed * 0.5 +
        (30 if forest else 0) +
        max(0, 50 - params.soil_moisture) * 0.4
    ))
    cyclone = min(100, (
        params.wind_speed * 0.85 +
        params.rainfall * 0.18 +
        (35 if coastal else 0) +
        params.humidity * 0.08
    )) if coastal else params.wind_speed * 0.25
    landslide = min(100, (
        params.rainfall * 0.42 +
        params.soil_moisture * 0.28 +
        max(0, elev - 200) * 0.04 +
        (20 if forest else 0) +
        params.seismic_activity * 3
    ))
    heatwave = min(100, (
        max(0, params.temperature - 30) * 4.5 +
        max(0, params.humidity - 55) * 0.4 +
        params.air_quality_index * 0.08
    ))
    drought = min(100, (
        max(0, 80 - params.rainfall) * 0.65 +
        max(0, params.temperature - 35) * 1.8 +
        max(0, 30 - params.humidity) * 0.7
    ))
    earthquake = min(100, params.seismic_activity * 10 + seismic_base)
    air_risk = min(100, params.air_quality_index * 0.22)
    fog_risk = min(100, max(0, (10 - params.visibility_km) * 8) + params.humidity * 0.15)
    tsunami_risk = min(100, (params.storm_surge * 5 + params.seismic_activity * 4)) if coastal else 0

    risks = {
        "flood": round(flood, 1),
        "fire": round(fire, 1),
        "cyclone": round(cyclone, 1),
        "landslide": round(landslide, 1),
        "heatwave": round(heatwave, 1),
        "drought": round(drought, 1),
        "earthquake": round(earthquake, 1),
        "air_quality": round(air_risk, 1),
        "fog": round(fog_risk, 1),
        "tsunami": round(tsunami_risk, 1),
    }
    overall = round(max(risks.values()) * 0.45 + sum(risks.values()) / len(risks) * 0.55, 1)
    level = "CRITICAL" if overall > 70 else "HIGH" if overall > 50 else "MODERATE" if overall > 30 else "LOW"
    dominant = max(risks, key=risks.get)
    return {"risks": risks, "overall": overall, "level": level, "dominant": dominant}

def get_risk_factors(params: RiskRequest, risks: dict) -> list:
    factors = []
    if params.rainfall > 100: factors.append(f"Extreme rainfall {params.rainfall}mm/hr — flash flood potential")
    if params.temperature > 40: factors.append(f"Dangerous heat {params.temperature}°C — heat stroke risk")
    if params.wind_speed > 60: factors.append(f"Severe winds {params.wind_speed}km/h — structural damage risk")
    if params.river_level > 70: factors.append(f"River near overflow {params.river_level}% — evacuate flood plains")
    if params.humidity > 85: factors.append(f"High humidity {params.humidity}% — disease outbreak risk")
    if params.seismic_activity > 4: factors.append(f"Seismic activity Richter {params.seismic_activity} — aftershocks possible")
    if params.air_quality_index > 200: factors.append(f"Hazardous AQI {params.air_quality_index} — respiratory emergency")
    if params.soil_moisture > 80: factors.append(f"Saturated soil {params.soil_moisture}% — landslide/mudslide risk")
    if params.visibility_km < 3: factors.append(f"Low visibility {params.visibility_km}km — transport hazard")
    if params.storm_surge > 3: factors.append(f"Storm surge {params.storm_surge}m — coastal inundation imminent")
    return factors or ["Conditions within normal acceptable range"]

# ─── NLP SOS Engine ──────────────────────────────────────────────────────────
DISTRESS_KEYWORDS = {
    "flood":     ["flood","flooding","water rising","submerged","inundated","drowning","swept","overflowing","water level","stuck in water","knee deep","waist deep","marooned"],
    "fire":      ["fire","burning","flames","smoke","wildfire","blaze","inferno","engulfed","explosion","gas leak"],
    "cyclone":   ["cyclone","storm","hurricane","typhoon","strong winds","gale","tornado","roof blown","wind damage"],
    "earthquake":["earthquake","tremor","shaking","quake","collapsed","building fell","crack","rubble"],
    "landslide": ["landslide","mudslide","debris","hill collapsed","slope failure","avalanche","rocks falling"],
    "medical":   ["injured","medical","hospital","ambulance","hurt","casualties","dead","unconscious","heart attack","stroke","bleeding"],
    "trapped":   ["trapped","stuck","stranded","rescue","help","sos","mayday","emergency","please help","save us","can't escape","surrounded"],
    "tsunami":   ["tsunami","tidal wave","sea surge","wave","ocean flooding"],
}
LOCATION_KEYWORDS = list(CITIES.keys()) + [
    "Kerala","Maharashtra","Gujarat","Tamil Nadu","Karnataka","Andhra Pradesh",
    "Assam","Odisha","Bihar","Rajasthan","Uttarakhand","Himachal Pradesh",
    "West Bengal","Telangana","Madhya Pradesh","Chhattisgarh","Manipur","J&K"
]

def analyze_sos(message: str) -> dict:
    msg_lower = message.lower()
    detected = []
    for dtype, kws in DISTRESS_KEYWORDS.items():
        if any(kw in msg_lower for kw in kws):
            detected.append(dtype)
    is_distress = bool(detected) or any(s in msg_lower for s in ["help","sos","emergency","danger","urgent"])
    if is_distress and not detected:
        detected = ["general_emergency"]
    location = None
    lat, lng = None, None
    for loc in LOCATION_KEYWORDS:
        if loc.lower() in msg_lower:
            location = loc
            if loc in CITIES:
                lat = CITIES[loc]["lat"] + random.uniform(-0.08, 0.08)
                lng = CITIES[loc]["lng"] + random.uniform(-0.08, 0.08)
            break
    severity = 3 if any(w in msg_lower for w in ["critical","dying","dead","severe","extreme","multiple","many"]) else \
               2 if any(w in msg_lower for w in ["urgent","dangerous","serious","trapped","stuck","please"]) else 1
    priority = "P1-CRITICAL" if severity == 3 else "P2-HIGH" if severity == 2 else "P3-MODERATE"
    actions = []
    if "flood" in detected: actions += ["Deploy NDRF flood rescue team","Activate water pumping stations","Evacuate low-lying areas","Position helicopters for aerial rescue"]
    if "fire" in detected: actions += ["Dispatch fire brigade — Dial 101","Alert forest department","Establish fire break lines","Evacuate 500m radius"]
    if "medical" in detected: actions += ["Dispatch ambulance — Dial 108","Alert nearest trauma centre","Send paramedic first responder","Blood bank alert if mass casualty"]
    if "trapped" in detected: actions += ["Deploy search & rescue team","Send USAR (Urban Search & Rescue)","Dispatch drone for aerial survey","Establish communication relay"]
    if "earthquake" in detected: actions += ["Deploy NDRF structural collapse team","Heavy machinery for rubble clearing","Medical triage centre setup","Gas & power line shut-off"]
    if not actions: actions = ["Dispatch multi-hazard response team","Conduct aerial survey via drone","Alert District Emergency Operations Centre","Coordinate with local police"]
    return {
        "is_distress": is_distress,
        "types": detected,
        "location": location,
        "lat": lat, "lng": lng,
        "severity": severity,
        "priority": priority,
        "recommended_actions": actions[:5],
        "confidence": round(min(99, len(detected)*28 + severity*15 + 10), 1),
        "estimated_victims": random.randint(5, 200) if severity >= 2 else random.randint(1, 20),
        "response_eta_mins": random.randint(15, 45) if priority == "P1-CRITICAL" else random.randint(30, 90),
    }

# ─── Forecast Engine ──────────────────────────────────────────────────────────
def generate_forecast(city: str, hours: int = 72) -> dict:
    city_data = CITIES.get(city, {})
    month = datetime.now().month
    is_monsoon = 6 <= month <= 9
    is_cyclone_season = month in [10, 11] and city_data.get("coastal", False)
    is_heat_season = month in [4, 5, 6]

    base = {
        "flood":     35 + (30 if is_monsoon else 0),
        "fire":      25 + (25 if is_heat_season else 0),
        "cyclone":   15 + (40 if is_cyclone_season else 0),
        "landslide": 20 + (22 if is_monsoon and city_data.get("elev",0)>400 else 0),
        "heatwave":  15 + (35 if is_heat_season else 0),
        "earthquake":city_data.get("zone_risk", 10),
        "air_quality":25,
    }
    points = []
    for h in range(0, hours+1, 3):
        dt = datetime.now() + timedelta(hours=h)
        wave = math.sin(h * 0.18) * 12 + math.cos(h * 0.09) * 6
        hour_risks = {}
        for k, v in base.items():
            jitter = random.uniform(-6, 6)
            adjusted = max(5, min(95, v + wave + jitter))
            # Diurnal: floods/landslides worse at night, fire worse in afternoon
            if k in ["flood","landslide"] and 18 <= dt.hour <= 24: adjusted = min(95, adjusted + 8)
            if k == "fire" and 12 <= dt.hour <= 17: adjusted = min(95, adjusted + 10)
            hour_risks[k] = round(adjusted, 1)
        overall = round(max(hour_risks.values()) * 0.4 + sum(hour_risks.values())/len(hour_risks) * 0.6, 1)
        points.append({
            "hour": h, "time": dt.strftime("%Y-%m-%d %H:%M"),
            "label": f"+{h}h" if h else "Now",
            "risks": hour_risks, "overall": overall,
            "level": "CRITICAL" if overall>70 else "HIGH" if overall>50 else "MODERATE" if overall>30 else "LOW"
        })
    peak = max(points, key=lambda x: x["overall"])
    season = "Monsoon" if is_monsoon else "Pre-Monsoon" if month in [4,5] else "Cyclone Season" if is_cyclone_season else "Winter/Post-Monsoon"
    return {"forecast": points, "peak": peak, "season": season, "city": city}

# ─── Impact Analysis Engine ──────────────────────────────────────────────────
def compute_impact(city: str, disaster_type: str, magnitude: float, duration_hours: int) -> dict:
    city_data = CITIES.get(city, {})
    pop = city_data.get("pop", 1000000)
    factor = magnitude / 100
    duration_factor = min(3, duration_hours / 24)

    casualties_estimate = int(pop * factor * 0.0002 * duration_factor)
    displaced = int(pop * factor * 0.05 * duration_factor)
    infrastructure_damage = round(factor * duration_factor * random.uniform(500, 5000), 0)
    economic_loss = round(infrastructure_damage * random.uniform(3, 8), 0)
    response_days = max(3, int(magnitude / 15 + duration_hours / 48))

    sector_impacts = {
        "Housing":        round(factor * 80, 1),
        "Transport":      round(factor * 65, 1),
        "Power Grid":     round(factor * 55, 1),
        "Healthcare":     round(factor * 45, 1),
        "Agriculture":    round(factor * 70, 1),
        "Communication":  round(factor * 40, 1),
        "Water Supply":   round(factor * 60, 1),
        "Education":      round(factor * 35, 1),
    }

    return {
        "city": city, "disaster_type": disaster_type,
        "magnitude": magnitude, "duration_hours": duration_hours,
        "estimated_casualties": f"{casualties_estimate:,}",
        "displaced_persons": f"{displaced:,}",
        "infrastructure_damage_cr": f"₹{infrastructure_damage:,.0f} Cr",
        "economic_loss_cr": f"₹{economic_loss:,.0f} Cr",
        "recovery_days": response_days,
        "sector_impacts": sector_impacts,
        "aid_requirements": {
            "food_rations": f"{displaced * 3:,} packets/day",
            "water_litres": f"{displaced * 15:,} L/day",
            "medical_teams": max(5, int(casualties_estimate / 50)),
            "shelter_units": max(100, int(displaced / 8)),
            "helicopters": max(2, int(magnitude / 25)),
        }
    }

# ─── Evacuation Planner ───────────────────────────────────────────────────────
def plan_evacuation(city: str, disaster_type: str, severity: float, pop_affected: int) -> dict:
    city_data = CITIES.get(city, {})
    state = city_data.get("state", "Unknown")
    
    phases = [
        {"phase": 1, "label": "Immediate (0–2 hrs)", "action": "Activate EOC. Issue public alert via SMS, All India Radio, DD News. NDRF teams mobilized.", "population": int(pop_affected * 0.3)},
        {"phase": 2, "label": "Evacuation (2–8 hrs)", "action": "Deploy buses, trucks. Open 15+ relief shelters. Establish pickup points. Disable power in flood zones.", "population": int(pop_affected * 0.5)},
        {"phase": 3, "label": "Rescue (8–24 hrs)",   "action": "Aerial survey. Search & rescue in critical zones. Medical triage centres. Relief distribution.", "population": int(pop_affected * 0.15)},
        {"phase": 4, "label": "Relief (24–72 hrs)",  "action": "Full relief operations. Damage assessment. Restoration of essential services. Mass counselling.", "population": int(pop_affected * 0.05)},
    ]
    
    routes = [
        {"route": f"NH-{random.randint(1,100)}", "direction": random.choice(["North","South","East","West"]), "capacity_per_hr": random.randint(500, 3000), "status": random.choice(["OPEN","OPEN","OPEN","CONGESTED"])},
        {"route": f"SH-{random.randint(1,50)}", "direction": random.choice(["North","South","East","West"]), "capacity_per_hr": random.randint(200, 1500), "status": random.choice(["OPEN","OPEN","CONGESTED"])},
        {"route": f"City Ring Road", "direction": "Bypass", "capacity_per_hr": random.randint(1000, 4000), "status": random.choice(["OPEN","OPEN","BLOCKED"])},
    ]
    
    shelters = [
        {"name": f"{city} Government School Complex", "capacity": 2500, "lat": city_data["lat"]+0.03, "lng": city_data["lng"]+0.03, "status": "OPEN"},
        {"name": f"{state} Stadium Relief Centre", "capacity": 8000, "lat": city_data["lat"]-0.02, "lng": city_data["lng"]+0.05, "status": "OPEN"},
        {"name": f"Community Hall Sector-A", "capacity": 1500, "lat": city_data["lat"]+0.01, "lng": city_data["lng"]-0.04, "status": "OPEN"},
        {"name": f"{city} College Ground", "capacity": 3000, "lat": city_data["lat"]-0.04, "lng": city_data["lng"]-0.02, "status": "PARTIAL"},
    ]
    
    return {
        "city": city, "disaster_type": disaster_type, "severity": severity,
        "total_to_evacuate": f"{pop_affected:,}",
        "estimated_completion_hrs": max(6, int(pop_affected / 5000)),
        "phases": phases, "evacuation_routes": routes, "shelters": shelters,
        "emergency_contacts": {
            "NDRF": "011-23438252",
            "State Control Room": f"1077",
            "Police": "100", "Ambulance": "108", "Fire": "101",
            "Women Helpline": "1091", "Child Helpline": "1098"
        }
    }

# ─── Resource Allocation ──────────────────────────────────────────────────────
RESOURCES = {
    "flood":     [("NDRF Rescue Boats",35000),("Water Pumping Units",25000),("Medical Teams",150000),("Helicopters",2500000),("Relief Shelters",80000),("Life Jackets",3000),("Rubber Rafts",45000)],
    "fire":      [("Fire Brigade Units",800000),("Water Tankers",200000),("Forest Dept Teams",120000),("Water Bomber Aircraft",5000000),("Breathing Apparatus",15000),("Fire Retardant Chemical",50000)],
    "cyclone":   [("Evacuation Buses",900000),("Cyclone Shelters",300000),("Coast Guard Vessels",2000000),("Relief Kits",1500),("Sand Bags",500),("Emergency Generators",80000)],
    "earthquake":[("USAR Teams",200000),("Heavy Machinery",1500000),("Medical Emergency Teams",180000),("Tents/Temporary Shelters",25000),("Search Dogs",50000),("Thermal Cameras",200000)],
    "landslide": [("Geological Survey Teams",150000),("Excavators",2000000),("Search & Rescue Teams",180000),("Medical Teams",150000),("Rope & Climbing Gear",20000)],
    "heatwave":  [("Mobile Medical Vans",500000),("Cooling Centres",100000),("ORS Packets",200),("Ice Block Supply",5000),("Awareness Teams",30000)],
}

def allocate_resources(city: str, disaster_type: str, severity: float) -> dict:
    city_data = CITIES.get(city, {})
    pop = city_data.get("pop", 1000000)
    pop_f = min(3, max(0.5, pop / 2000000))
    resource_list = RESOURCES.get(disaster_type, RESOURCES["flood"])
    allocations = []
    total_cost = 0
    for name, unit_cost in resource_list:
        base = max(2, int(severity / 15))
        count = int(base * pop_f)
        cost = count * unit_cost
        total_cost += cost
        allocations.append({
            "resource": name, "count": count,
            "unit_cost": f"₹{unit_cost:,}", "total_cost": f"₹{cost:,}",
            "deployment_time": f"{random.randint(15,120)} mins",
            "priority": "IMMEDIATE" if severity > 60 else "HIGH" if severity > 40 else "STANDARD",
            "source": random.choice(["State Reserve","Central Pool","District Stock","Rapid Mobilization"])
        })
    return {
        "city": city, "state": city_data.get("state",""),
        "disaster_type": disaster_type, "severity": severity,
        "allocations": allocations,
        "total_estimated_cost": f"₹{total_cost:,}",
        "deployment_zones": [f"Zone {chr(65+i)}" for i in range(min(6, max(2, int(severity/18))))],
        "estimated_affected_pop": f"{int(pop * severity / 600):,}",
        "evacuation_radius_km": round(severity / 10, 1),
        "command_centre": f"{city} District Collector Office",
    }

# ─── Historical Events ─────────────────────────────────────────────────────────
HISTORICAL = {
    "Mumbai":       [("1994 Plague",1994,"epidemic","900 deaths, city shutdown"),("2005 Floods",2005,"flood","1094 deaths, ₹550 Cr damage"),("2006 Train Blasts",2006,"manmade","209 deaths"),],
    "Chennai":      [("2004 Indian Ocean Tsunami",2004,"tsunami","Massive coastal destruction"),("2015 Floods",2015,"flood","500 deaths, ₹20,000 Cr damage"),],
    "Wayanad":      [("2018 Floods & Landslide",2018,"landslide","500+ deaths, 2.68L displaced"),("2019 Floods",2019,"flood","Severe flooding across district"),],
    "Uttarakhand":  [("2013 Kedarnath Floods",2013,"flood","5700+ deaths, Himalayan catastrophe"),("2021 Chamoli Glacial Burst",2021,"landslide","200 deaths, glacial lake outburst"),],
    "Bhubaneswar":  [("1999 Odisha Super Cyclone",1999,"cyclone","10000+ deaths, 15M displaced"),("2013 Cyclone Phailin",2013,"cyclone","Massive evac — 12 deaths due to preparedness"),],
    "Guwahati":     [("2012 Assam Floods",2012,"flood","100+ deaths, 2.5M displaced"),("2015 Floods",2015,"flood","Severe Brahmaputra flooding"),],
    "Delhi":        [("1988 Delhi Floods",1988,"flood","Yamuna overflowed, massive damage"),("2023 Floods",2023,"flood","Yamuna record high, 26,000 displaced"),],
    "Kochi":        [("2018 Kerala Floods",2018,"flood","483 deaths, worst in 100 years"),("2019 Floods",2019,"flood","Third consecutive year of floods"),],
}

# ─── Groq AI ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are IRIS v4.0 — India's premier AI Disaster Intelligence System. You are a highly trained expert in:

🌊 DISASTER DOMAINS: Floods, cyclones, earthquakes, landslides, heatwaves, droughts, tsunamis, wildfires, industrial disasters, urban flooding

🇮🇳 INDIA-SPECIFIC KNOWLEDGE:
- All 28 states and 8 UTs, their vulnerability profiles
- Indian geography: Western Ghats, Himalayas, Indo-Gangetic Plain, Coastal zones
- Rivers: Ganga, Brahmaputra, Godavari, Krishna, Cauvery, Indus, Mahanadi
- Seismic zones I-V across India
- Monsoon patterns: SW Monsoon (Jun-Sep), NE Monsoon (Oct-Dec for south India)
- Bay of Bengal and Arabian Sea cyclone seasons

🏛️ AGENCIES & SYSTEMS:
- NDRF (National Disaster Response Force) — 16 battalions
- SDRF (State Disaster Response Force)
- NDMA (National Disaster Management Authority)
- IMD (Indian Meteorological Department)
- INCOIS (Indian National Centre for Ocean Information Services) — tsunami warnings
- NRSC/ISRO — satellite monitoring
- Central Water Commission — flood forecasting

📋 RESPONSE PROTOCOLS:
- ICS (Incident Command System)
- Standard Operating Procedures for each disaster type
- NDMA guidelines
- Inter-agency coordination frameworks

RESPONSE STYLE:
- Be specific, actionable, and concise
- Use bullet points for action items
- Reference exact Indian agencies, helplines (NDRF: 011-23438252, Police: 100, Ambulance: 108, Fire: 101)
- Cite geographic specifics (rivers, hills, coastal proximity)
- For technical queries: provide data-backed answers
- For emergency queries: lead with IMMEDIATE actions first
- Always end with a confidence level (High/Medium/Low) and source

For BRIEFING mode: Give a structured situation report (SITREP) format
For EMERGENCY mode: Lead with immediate life-safety actions only
For TECHNICAL mode: Deep dive into methodology and data"""

def get_groq_response(message: str, city: Optional[str], context: Optional[Dict], history: Optional[List], mode: str = "general") -> str:
    client = get_groq_client()
    if not client:
        return generate_fallback_response(message, city, context, mode)
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if city or context:
        ctx = "=== CURRENT SITUATIONAL DATA ===\n"
        if city and city in CITIES:
            d = CITIES[city]
            ctx += f"Location: {city}, {d['state']}\n"
            ctx += f"Population: {d['pop']:,} | Elevation: {d['elev']}m | Seismic Zone: {d['zone']}\n"
            ctx += f"Coastal: {d['coastal']} | River: {d['river']} | Forest: {d['forest']}\n"
            ctx += f"Annual Rainfall: {d['annual_rain']}mm\n"
        if context:
            if "risks" in context:
                ctx += f"Current Risk Matrix: {json.dumps(context['risks'])}\n"
            if "overall" in context:
                ctx += f"Overall Risk: {context['overall']}% ({context.get('level','')})\n"
            if "dominant" in context:
                ctx += f"Primary Threat: {context.get('dominant','').upper()}\n"
        ctx += f"Mode: {mode.upper()} | Time: {datetime.now().strftime('%H:%M IST %d-%b-%Y')}\n"
        messages.append({"role": "user", "content": ctx})
        messages.append({"role": "assistant", "content": "Situational data received. Ready to provide analysis."})

    if history:
        for h in history[-8:]:
            messages.append({"role": h["role"], "content": h["content"]})
    else:
        messages.append({"role": "user", "content": message})

    try:
        resp = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=900,
            temperature=0.65,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return generate_fallback_response(message, city, context, mode)

def generate_fallback_response(msg: str, city: Optional[str], context: Optional[Dict], mode: str) -> str:
    m = msg.lower()
    city_str = city or "the region"
    ctx_str = ""
    if context and "overall" in context:
        ctx_str = f"\n\n**Current Assessment:** {context.get('city',city_str)} — {context['overall']}% risk ({context.get('level','')}), primary threat: **{context.get('dominant','').upper()}**"

    if "briefing" in mode or "sitrep" in m or "brief" in m:
        return f"""📋 **SITUATION REPORT (SITREP) — {city_str.upper()}**
*{datetime.now().strftime('%H:%M IST, %d %b %Y')}*

**SITUATION OVERVIEW:**
Active monitoring of disaster risk parameters for {city_str}. Multi-hazard assessment running continuously.

**CURRENT THREAT LEVEL:** {context.get('level','UNKNOWN') if context else 'Pending analysis'}
**PRIMARY HAZARD:** {context.get('dominant','Run analysis first').upper() if context else 'Run analysis first'}

**KEY OBSERVATIONS:**
• IMD weather bulletins being monitored every 3 hours
• NDRF teams on readiness level based on risk index
• District EOC operational and staffed

**RECOMMENDED NEXT STEPS:**
• Run full risk analysis to update threat matrix
• Check 72-hour forecast tab for trend analysis
• Review resource allocation for primary threat type

**Confidence:** Medium | *Connect GROQ_API_KEY for full AI analysis*{ctx_str}"""

    if any(w in m for w in ["flood","flooding","water"]):
        return f"""🌊 **FLOOD RESPONSE PROTOCOL — {city_str}**

**IMMEDIATE (0–2 hrs):**
• Issue Red/Orange alert via IMD/NDMA systems
• Deploy NDRF boats and rescue teams
• Activate Emergency Operations Centre
• Alert hospitals: prepare for mass casualty

**EVACUATION (2–8 hrs):**
• Evacuate flood plains & low-lying areas first
• Open government schools/stadiums as shelters
• Deploy buses at designated pickup points
• Disable electrical supply in inundated zones

**PUBLIC ADVISORY:**
• Move to upper floors or high ground
• Never walk/drive through floodwater
• Keep emergency kit: documents, medicines, water
• Monitor All India Radio / DD News

📞 **NDRF Helpline: 011-23438252 | Flood Control: 1800-180-5656**{ctx_str}

*Confidence: High | Source: NDRF SOP Rev.2024*"""

    if any(w in m for w in ["cyclone","storm"]):
        return f"""🌀 **CYCLONE RESPONSE PROTOCOL — {city_str}**

**PRE-CYCLONE (48–72 hrs):**
• Issue Cyclone Watch/Warning (IMD category system)
• Evacuate coastal areas within 5km of shoreline
• Secure fishing vessels in designated harbors
• Stock 72-hour emergency supplies

**DURING CYCLONE:**
• Stay in strong structures, away from windows
• Do not venture out during eye of storm passage
• Monitor IMD Cyclone Track: **rsmcnewdelhi.imd.gov.in**

**POST-CYCLONE:**
• Beware of downed power lines
• Report damaged structures before entering
• Watch for secondary flooding and landslides

📞 **Coast Guard: 1554 | NDRF: 011-23438252**{ctx_str}

*Confidence: High | Source: IMD Cyclone Warning Services*"""

    if any(w in m for w in ["earthquake","tremor","quake"]):
        return f"""⚡ **EARTHQUAKE RESPONSE PROTOCOL**

**DURING SHAKING:**
• Drop, Cover, Hold — under desk/table
• Stay away from windows and exterior walls
• If outdoors: move away from buildings

**IMMEDIATELY AFTER:**
• Check for injuries — do not move severely injured
• Shut off gas if leak suspected
• Do not use elevators
• Expect aftershocks — stay prepared

**RESCUE OPERATIONS:**
• NDRF USAR (Urban Search & Rescue) deployment
• Heavy machinery for structural collapse
• Thermal cameras for survivor detection
• Medical triage on-site before hospital transfer

📞 **NDRF: 011-23438252 | NDRMA: 011-26701700**{ctx_str}"""

    if any(w in m for w in ["safe","risk","status","level","danger"]):
        if context and "overall" in context:
            level = context.get("level","")
            overall = context.get("overall",0)
            dom = context.get("dominant","")
            advice = {"CRITICAL":"🔴 EVACUATE immediately. Do not wait.","HIGH":"🟠 Prepare emergency kit. Monitor alerts closely.","MODERATE":"🟡 Stay informed. No immediate action needed.","LOW":"🟢 Normal conditions. Maintain standard preparedness."}
            return f"""📊 **SAFETY ASSESSMENT — {city_str.upper()}**

**Overall Risk Index:** {overall}% → **{level}**
**Primary Threat:** {dom.upper()}

**Status:** {advice.get(level,'Monitor conditions.')}

**Monitoring Points:**
• IMD weather bulletins every 3 hours
• Local river gauge stations (Central Water Commission)
• District Collector emergency notifications
• NDMA mobile alerts (register: mha.gov.in/ndma)

*Last computed: {datetime.now().strftime('%H:%M IST')} | Next update in 60 mins*"""
        return f"Please run a **Risk Analysis** first (left panel → select city → click ANALYZE). Then I can give you a precise safety assessment for {city_str}."

    return f"""🤖 **IRIS v4.0 — Disaster Intelligence System**

I'm your AI-powered emergency management assistant for India.

**What I can help with:**
• 📊 Real-time risk assessment & analysis
• 🌊 Disaster-specific response protocols (flood, cyclone, earthquake, fire...)
• 🚁 Resource allocation & deployment planning
• 🗺 Evacuation route planning
• 📈 72-hour risk forecasting
• 📰 Historical disaster analysis
• 💰 Economic impact estimation

**Quick commands:**
• *"Is {city_str} safe from flooding?"*
• *"SITREP for {city_str}"* — full situation report
• *"What resources needed for cyclone response?"*
• *"Evacuation plan for {city_str}"*

*Connect GROQ_API_KEY for full AI-powered responses.*"""

# ─── News/Intelligence Feed ───────────────────────────────────────────────────
NEWS_TEMPLATES = [
    ("{city}", "ALERT", "IMD issues {color} alert for {city} due to heavy rainfall forecast in next 24 hours. Residents advised to stay vigilant."),
    ("{city}", "UPDATE", "NDRF team deployed to {city} district following reports of flash flooding. Rescue operations underway."),
    ("{city}", "CLEAR", "Flood waters receding in {city}. Normalcy expected to return within 48 hours as relief operations continue."),
    ("{city}", "ALERT", "Cyclone watch issued for coastal {city}. Fishing activity suspended. Evacuation of low-lying areas underway."),
    ("{city}", "UPDATE", "Air quality index in {city} reaches hazardous level {aqi}. Schools closed. Public advised to avoid outdoor activity."),
    ("{city}", "NDRF", "NDRF Battalion 7 deployed to {city} for flood relief. 3 rescue boats operational. {n} persons evacuated."),
    ("{city}", "IMD", "IMD Doppler radar detects intense convective activity near {city}. Thunderstorm warning for next 6 hours."),
    ("{city}", "CLEAR", "Earthquake of magnitude {mag} recorded near {city}. No major damage reported. NDMA monitoring for aftershocks."),
]

def generate_news_feed(city: Optional[str], dtype: Optional[str]) -> list:
    cities_pool = [city] * 4 + list(CITIES.keys()) if city else list(CITIES.keys())
    items = []
    for _ in range(15):
        tmpl = random.choice(NEWS_TEMPLATES)
        c = random.choice(cities_pool)
        _, level, text = tmpl
        text = text.format(city=c, color=random.choice(["Red","Orange","Yellow"]),
                           aqi=random.randint(201,400), n=random.randint(50,2000),
                           mag=round(random.uniform(3.0,6.5),1))
        time_ago = random.randint(2, 180)
        items.append({
            "id": f"NEWS-{random.randint(1000,9999)}",
            "city": c, "level": level, "text": text,
            "time_ago_mins": time_ago,
            "timestamp": (datetime.now() - timedelta(minutes=time_ago)).strftime("%H:%M"),
            "source": random.choice(["IMD","NDRF","State EOC","ANI","PTI","NDMA"])
        })
    items.sort(key=lambda x: x["time_ago_mins"])
    return items

# ─── WebSocket Manager ────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
    async def broadcast(self, data: dict):
        for conn in self.active[:]:
            try: await conn.send_json(data)
            except: self.disconnect(conn)

manager = ConnectionManager()

# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status":"IRIS v4.0 OPERATIONAL","endpoints":15,"cities":len(CITIES),"version":"4.0.0"}

@app.post("/analyze-risk")
def analyze_risk(req: RiskRequest):
    if req.city not in CITIES:
        raise HTTPException(400, f"Unknown city")
    city_data = CITIES[req.city]
    result = compute_risks(city_data, req)
    factors = get_risk_factors(req, result["risks"])
    historical = [{"event":e,"year":y,"type":t,"impact":i,"years_ago":datetime.now().year-y} for e,y,t,i in HISTORICAL.get(req.city,[])]
    alerts = [{"type":k,"score":v,"level":"CRITICAL" if v>70 else "HIGH","action":f"Immediate {k} response"} for k,v in result["risks"].items() if v>50]
    seismic_zone = city_data.get("zone","N/A")
    return {
        **result, "city": req.city, "state": city_data["state"],
        "population": city_data["pop"], "lat": city_data["lat"], "lng": city_data["lng"],
        "seismic_zone": seismic_zone, "annual_rainfall_mm": city_data["annual_rain"],
        "risk_factors": factors, "active_alerts": alerts,
        "historical_context": historical,
        "timestamp": datetime.now().isoformat(),
        "imd_station": f"{req.city} Meteorological Centre",
        "next_update": (datetime.now() + timedelta(hours=1)).isoformat()
    }

@app.post("/sos-detect")
def sos_detect(req: SOSRequest):
    result = analyze_sos(req.message)
    if result["is_distress"]:
        result["incident_id"] = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100,999)}"
        result["auto_alert_sent"] = True
        result["response_agencies"] = ["NDRF","State SDRF","District Collector","Local Police","Medical Emergency"]
        result["dispatch_time"] = datetime.now().strftime("%H:%M:%S IST")
    return result

@app.post("/chat")
def chat(req: ChatRequest):
    msgs = req.history or []
    if req.message: msgs.append({"role":"user","content":req.message})
    response = get_groq_response(req.message, req.city, req.context, req.history, req.mode)
    return {"response": response, "city": req.city, "mode": req.mode, "model":"llama3-70b-8192", "timestamp": datetime.now().isoformat()}

@app.post("/forecast")
def forecast(req: EarlyWarningRequest):
    if req.city not in CITIES: raise HTTPException(400,"Unknown city")
    return generate_forecast(req.city, req.hours_ahead)

@app.post("/resource-allocation")
def resource_allocation(req: ResourceRequest):
    if req.city not in CITIES: raise HTTPException(400,"Unknown city")
    return allocate_resources(req.city, req.disaster_type, req.severity)

@app.post("/impact-analysis")
def impact_analysis(req: ImpactRequest):
    if req.city not in CITIES: raise HTTPException(400,"Unknown city")
    return compute_impact(req.city, req.disaster_type, req.magnitude, req.duration_hours)

@app.post("/evacuation-plan")
def evacuation_plan(req: EvacuationRequest):
    if req.city not in CITIES: raise HTTPException(400,"Unknown city")
    return plan_evacuation(req.city, req.disaster_type, req.severity, req.population_affected)

@app.get("/all-cities-risk")
def all_cities_risk():
    month = datetime.now().month
    is_monsoon = 6 <= month <= 9
    results = []
    for city, data in CITIES.items():
        base = 30 + (random.randint(10,45) if is_monsoon else random.randint(0,25))
        overall = max(5, min(95, base + random.randint(-10,10)))
        level = "CRITICAL" if overall>70 else "HIGH" if overall>50 else "MODERATE" if overall>30 else "LOW"
        results.append({"city":city,"lat":data["lat"],"lng":data["lng"],"state":data["state"],"overall_risk":overall,"level":level,"dominant":random.choice(["flood","fire","cyclone","heatwave","earthquake"])})
    return {"cities":results,"total":len(results),"timestamp":datetime.now().isoformat()}

@app.post("/generate-alert")
def generate_alert(req: ResourceRequest):
    city_data = CITIES.get(req.city,{})
    sev = "RED" if req.severity>70 else "ORANGE" if req.severity>50 else "YELLOW"
    pop = city_data.get("pop",1000000)
    agencies = ["NDRF","SDRF",f"{city_data.get('state','')} DM","IMD","District Collector"]
    if req.severity > 70: agencies.append("Armed Forces (on standby)")
    return {
        "alert_id": f"IRIS-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "severity": sev, "district": req.city, "state": city_data.get("state",""),
        "disaster_type": req.disaster_type.upper(), "risk_score": req.severity,
        "message": f"{'🔴 RED ALERT' if sev=='RED' else '🟠 ORANGE WARNING' if sev=='ORANGE' else '🟡 YELLOW ADVISORY'}: {req.disaster_type.upper()} RISK {req.severity:.0f}% — {req.city}, {city_data.get('state','')}. ~{int(pop*req.severity/600):,} persons potentially affected.",
        "agencies_notified": agencies,
        "public_instructions": ["Tune to All India Radio / DD News","Keep emergency kit ready (72hr supplies)","Follow evacuation orders","NDRF Helpline: 011-23438252"],
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M IST")
    }

@app.get("/historical/{city}")
def get_historical(city: str):
    events = [{"event":e,"year":y,"type":t,"impact":i,"years_ago":datetime.now().year-y} for e,y,t,i in HISTORICAL.get(city,[])]
    return {"city":city,"events":events,"vulnerability_index":random.randint(35,85),"preparedness_score":random.randint(40,90)}

@app.post("/news-feed")
def news_feed(req: NewsRequest):
    return {"items": generate_news_feed(req.city, req.disaster_type), "generated_at": datetime.now().isoformat()}

@app.get("/cities")
def get_cities():
    return {"cities": {k:{"state":v["state"],"lat":v["lat"],"lng":v["lng"],"pop":v["pop"]} for k,v in CITIES.items()}, "count": len(CITIES)}

@app.post("/compare-cities")
def compare_cities(req: MultiCityRequest):
    results = {}
    for city in req.cities:
        if city in CITIES:
            d = CITIES[city]
            overall = random.randint(20, 85)
            results[city] = {"lat":d["lat"],"lng":d["lng"],"state":d["state"],"overall_risk":overall,"level":"CRITICAL" if overall>70 else "HIGH" if overall>50 else "MODERATE" if overall>30 else "LOW","population":d["pop"]}
    return {"comparison":results,"count":len(results)}

@app.websocket("/ws/live-alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            cities_list = list(CITIES.keys())
            city = random.choice(cities_list)
            severity = random.randint(30, 95)
            alert = {
                "type": "live_alert",
                "city": city, "state": CITIES[city]["state"],
                "severity": severity,
                "level": "CRITICAL" if severity>70 else "HIGH" if severity>50 else "MODERATE",
                "disaster": random.choice(["flood","fire","cyclone","earthquake","landslide","heatwave"]),
                "timestamp": datetime.now().isoformat(),
                "message": f"Auto-detected risk spike in {city}"
            }
            await websocket.send_json(alert)
            await asyncio.sleep(8)
    except WebSocketDisconnect:
        manager.disconnect(websocket)