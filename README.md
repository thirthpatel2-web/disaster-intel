<div align="center">

# 🌪️ IRIS: Disaster Intelligence System

**A command-centre dashboard for Indian cities: risk scoring, early warnings, evacuation plans, resource allocation and an AI analyst, on one live map.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-live%20alerts-4A4A55)
![Leaflet](https://img.shields.io/badge/Leaflet-map-199900?logo=leaflet&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-charts-FF6384?logo=chartdotjs&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036)

</div>

```
city profile ──► multi-hazard risk model ──► forecast · impact · evacuation · resources ──► live map + AI analyst
```

## ✨ Features

| Module | What it gives you |
|---|---|
| 🗺️ **Live risk map** | Every tracked city scored and coloured on a Leaflet map |
| ⚠️ **Multi-hazard risk analysis** | Flood, fire, cyclone, heatwave and earthquake risk from each city's profile (elevation, coast, rivers, forest, seismic zone, annual rainfall, population) plus your scenario inputs |
| 🆘 **SOS detection** | Reads a free-text distress message, classifies the emergency type and locates the city it mentions |
| 📈 **72-hour early warning** | Hour-by-hour forecast curves |
| 💥 **Impact analysis** | Estimated casualties, displaced persons, economic and infrastructure loss (₹ crore), recovery days, and aid needs (food, water, shelters, medical teams, helicopters) |
| 🚍 **Evacuation planning** | Phased plan with routes, shelters, people to move, completion time, and NDRF / police / fire / ambulance contacts |
| 🚁 **Resource allocation** | Resource allocations, deployment zones, evacuation radius, command centre and estimated cost |
| 🏙️ **City comparison & history** | Side-by-side risk and past events |
| 🤖 **AI analyst** | Chat about risk, evacuation or resources (Groq LLM, with a built-in rule-based fallback when no key is set) |
| 📡 **Live alert feed** | WebSocket stream at `/ws/live-alerts` |

Cities covered include Mumbai, Delhi, Chennai, Kolkata, Bengaluru, Hyderabad, Pune, Ahmedabad, Jaipur, Surat, Wayanad, Uttarakhand, Bhubaneswar and Guwahati.

## 🚀 Quick start

```bash
git clone https://github.com/thirthpatel2-web/disaster-intel.git
cd disaster-intel/backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export GROQ_API_KEY=your_key_here   # optional (Windows: set GROQ_API_KEY=...); free key at console.groq.com
uvicorn main:app --reload --port 8000
```

Then open `frontend/index.html` in your browser. It talks to the API at `http://localhost:8000`.

## 🔌 API at a glance

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/analyze-risk` | Multi-hazard risk for a city + scenario |
| `POST` | `/sos-detect` | Classify a distress message |
| `POST` | `/forecast` | 72-hour early-warning curves |
| `POST` | `/impact-analysis` | Impact estimate for a disaster |
| `POST` | `/evacuation-plan` | Evacuation zones and timeline |
| `POST` | `/resource-allocation` | Resources needed |
| `POST` | `/generate-alert` | Formatted public alert |
| `POST` | `/chat` | AI analyst |
| `POST` | `/compare-cities` · `/news-feed` | Comparison and news-style feed |
| `GET` | `/cities` · `/all-cities-risk` · `/historical/{city}` | Reference data |
| `WS` | `/ws/live-alerts` | Live alert stream |

Interactive docs: `http://localhost:8000/docs`.

## 🧾 Honest notes

- This is a **prototype and simulation**. Live alerts, the news feed, the all-cities risk overview and parts of the forecasts are **randomly generated** for demonstration, not pulled from IMD, NDMA or other real data feeds.
- The city profiles (coordinates, population, elevation, seismic zone, rainfall) are static reference values.
- The AI analyst uses Groq's `llama-3.3-70b-versatile`; without a `GROQ_API_KEY` it answers with built-in rule-based responses.

## 👤 Author

Built by [Thirth Patel](https://github.com/thirthpatel2-web).
