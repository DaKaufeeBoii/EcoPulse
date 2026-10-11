import uuid
from datetime import datetime, timezone
from typing import List
from app.schemas.air import AirObservationCreate, AirAssessmentResponse


class AirService:
    @staticmethod
    def classify_aqi(observation: AirObservationCreate) -> AirAssessmentResponse:
        aqi = observation.aqi

        if aqi <= 50:
            category = "Good"
            risk_level = "low"
            health_implications = "Air quality is satisfactory, and air pollution poses little or no risk."
            precautions = [
                "Air quality is ideal for outdoor sports and activities.",
                "Safe to ventilate indoor living spaces.",
            ]
        elif aqi <= 100:
            category = "Moderate"
            risk_level = "moderate"
            health_implications = "Air quality is acceptable; however, some pollutants may affect a few hypersensitive individuals."
            precautions = [
                "Unusually sensitive individuals should consider reducing prolonged outdoor exertion.",
                "General public can continue normal outdoor activities.",
            ]
        elif aqi <= 150:
            category = "Unhealthy for Sensitive Groups"
            risk_level = "elevated"
            health_implications = "Members of sensitive groups (children, elderly, people with asthma/heart disease) may experience adverse effects."
            precautions = [
                "Sensitive groups should limit strenuous outdoor activities.",
                "Wear protective particulate masks (N95) near high-traffic corridors.",
                "Keep windows closed during peak traffic hours.",
            ]
        elif aqi <= 200:
            category = "Unhealthy"
            risk_level = "high"
            health_implications = "Everyone may begin to experience health effects; members of sensitive groups may experience more serious effects."
            precautions = [
                "Active children and adults should avoid prolonged outdoor exertion.",
                "Wear N95/FFP2 masks outdoors.",
                "Operate indoor HEPA air purifiers where available.",
                "Keep windows and doors securely closed.",
            ]
        elif aqi <= 300:
            category = "Very Unhealthy"
            risk_level = "very_high"
            health_implications = "Health alert: risk of health effects is increased for everyone."
            precautions = [
                "Avoid all outdoor physical and recreational activities.",
                "Wear certified high-filtration respirators when outside.",
                "Run indoor air purifiers at maximum filtration.",
                "Vulnerable groups should remain strictly indoors.",
            ]
        else:
            category = "Hazardous"
            risk_level = "severe"
            health_implications = "Health warning of emergency conditions: everyone is more likely to be seriously affected."
            precautions = [
                "Remain indoors and avoid all outdoor exposure.",
                "Seal doors and windows against particulate infiltration.",
                "Consult healthcare providers immediately if shortness of breath occurs.",
                "Refrain from opening outdoor ventilation dampers.",
            ]

        return AirAssessmentResponse(
            assessment_id=f"air_assess_{uuid.uuid4().hex[:12]}",
            location_id=observation.location_id,
            timestamp=observation.timestamp or datetime.now(timezone.utc),
            aqi=aqi,
            source=observation.source,
            dominant_pollutant=observation.dominant_pollutant,
            category=category,
            risk_level=risk_level,
            health_implications=health_implications,
            precautions=precautions,
        )
