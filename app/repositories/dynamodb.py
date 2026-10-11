import json
from decimal import Decimal
from typing import Optional, List, Any
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from app.repositories.base import BaseRepository
from app.schemas.water import (
    WaterReading,
    WaterAssessmentResponse,
    WaterLeakReport,
)
from app.schemas.air import AirAssessmentResponse
from app.schemas.waste import WasteEntry


def _float_to_decimal(obj: Any) -> Any:
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_float_to_decimal(v) for v in obj]
    return obj


def _decimal_to_float(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(v) for v in obj]
    return obj


class DynamoDBRepository(BaseRepository):
    def __init__(self, table_name: Optional[str] = None, region_name: Optional[str] = None):
        self.table_name = table_name or settings.dynamodb_table_name
        self.region_name = region_name or settings.aws_region
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
        self.table = self.dynamodb.Table(self.table_name)

    def save_water_reading(self, reading: WaterReading, idempotency_key: Optional[str] = None) -> WaterReading:
        item = {
            "PK": f"LOC#{reading.location_id}",
            "SK": f"WATER_READING#{reading.timestamp.isoformat()}#{reading.reading_id}",
            "GSI1PK": "ENTITY#WATER_READING",
            "GSI1SK": reading.timestamp.isoformat(),
            "entity_type": "water_reading",
            "reading_id": reading.reading_id,
            "location_id": reading.location_id,
            "timestamp": reading.timestamp.isoformat(),
            "cumulative_reading_liters": _float_to_decimal(reading.cumulative_reading_liters),
            "unit": reading.unit,
        }
        if idempotency_key:
            item["idempotency_key"] = idempotency_key

        self.table.put_item(Item=item)
        return reading

    def get_water_readings(self, location_id: Optional[str] = None) -> List[WaterReading]:
        if location_id:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"LOC#{location_id}",
                    ":sk_prefix": "WATER_READING#",
                },
            )
            items = response.get("Items", [])
        else:
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :gsi1pk",
                ExpressionAttributeValues={":gsi1pk": "ENTITY#WATER_READING"},
            )
            items = response.get("Items", [])

        results = []
        for it in items:
            it_clean = _decimal_to_float(it)
            results.append(
                WaterReading(
                    reading_id=it_clean["reading_id"],
                    location_id=it_clean["location_id"],
                    timestamp=it_clean["timestamp"],
                    cumulative_reading_liters=it_clean["cumulative_reading_liters"],
                    unit=it_clean["unit"],
                )
            )
        return results

    def save_water_assessment(
        self, assessment: WaterAssessmentResponse, location_id: Optional[str] = None
    ) -> WaterAssessmentResponse:
        loc = location_id or "default"
        item = {
            "PK": f"LOC#{loc}",
            "SK": f"WATER_ASSESSMENT#{assessment.timestamp.isoformat()}#{assessment.assessment_id}",
            "GSI1PK": "ENTITY#WATER_ASSESSMENT",
            "GSI1SK": assessment.timestamp.isoformat(),
            "entity_type": "water_assessment",
            "assessment_id": assessment.assessment_id,
            "location_id": loc,
            "timestamp": assessment.timestamp.isoformat(),
            "daily_usage_liters": _float_to_decimal(assessment.daily_usage_liters),
            "usage_per_person_liters": _float_to_decimal(assessment.usage_per_person_liters),
            "status": assessment.status,
            "severity": assessment.severity,
            "estimated_excess_liters": _float_to_decimal(assessment.estimated_excess_liters),
            "explanation": assessment.explanation,
            "recommendation": assessment.recommendation,
        }
        self.table.put_item(Item=item)
        return assessment

    def get_water_assessments(self, location_id: Optional[str] = None) -> List[WaterAssessmentResponse]:
        if location_id:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"LOC#{location_id}",
                    ":sk_prefix": "WATER_ASSESSMENT#",
                },
            )
            items = response.get("Items", [])
        else:
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :gsi1pk",
                ExpressionAttributeValues={":gsi1pk": "ENTITY#WATER_ASSESSMENT"},
            )
            items = response.get("Items", [])

        results = []
        for it in items:
            it_clean = _decimal_to_float(it)
            results.append(
                WaterAssessmentResponse(
                    assessment_id=it_clean["assessment_id"],
                    location_id=it_clean.get("location_id"),
                    timestamp=it_clean["timestamp"],
                    daily_usage_liters=it_clean["daily_usage_liters"],
                    usage_per_person_liters=it_clean["usage_per_person_liters"],
                    status=it_clean["status"],
                    severity=it_clean["severity"],
                    estimated_excess_liters=it_clean["estimated_excess_liters"],
                    explanation=it_clean["explanation"],
                    recommendation=it_clean["recommendation"],
                )
            )
        return results

    def save_leak_report(self, report: WaterLeakReport) -> WaterLeakReport:
        item = {
            "PK": f"LOC#{report.location_id}",
            "SK": f"WATER_LEAK#{report.timestamp.isoformat()}#{report.report_id}",
            "GSI1PK": "ENTITY#WATER_LEAK",
            "GSI1SK": report.timestamp.isoformat(),
            "entity_type": "water_leak",
            "report_id": report.report_id,
            "location_id": report.location_id,
            "timestamp": report.timestamp.isoformat(),
            "area": report.area,
            "description": report.description,
            "observed_severity": report.observed_severity,
            "status": report.status,
        }
        self.table.put_item(Item=item)
        return report

    def get_leak_reports(self, location_id: Optional[str] = None) -> List[WaterLeakReport]:
        if location_id:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"LOC#{location_id}",
                    ":sk_prefix": "WATER_LEAK#",
                },
            )
            items = response.get("Items", [])
        else:
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :gsi1pk",
                ExpressionAttributeValues={":gsi1pk": "ENTITY#WATER_LEAK"},
            )
            items = response.get("Items", [])

        results = []
        for it in items:
            it_clean = _decimal_to_float(it)
            results.append(
                WaterLeakReport(
                    report_id=it_clean["report_id"],
                    location_id=it_clean["location_id"],
                    timestamp=it_clean["timestamp"],
                    area=it_clean["area"],
                    description=it_clean["description"],
                    observed_severity=it_clean["observed_severity"],
                    status=it_clean.get("status", "open"),
                )
            )
        return results

    def save_air_assessment(self, assessment: AirAssessmentResponse) -> AirAssessmentResponse:
        item = {
            "PK": f"LOC#{assessment.location_id}",
            "SK": f"AIR_ASSESSMENT#{assessment.timestamp.isoformat()}#{assessment.assessment_id}",
            "GSI1PK": "ENTITY#AIR_ASSESSMENT",
            "GSI1SK": assessment.timestamp.isoformat(),
            "entity_type": "air_assessment",
            "assessment_id": assessment.assessment_id,
            "location_id": assessment.location_id,
            "timestamp": assessment.timestamp.isoformat(),
            "aqi": assessment.aqi,
            "source": assessment.source,
            "dominant_pollutant": assessment.dominant_pollutant,
            "category": assessment.category,
            "risk_level": assessment.risk_level,
            "health_implications": assessment.health_implications,
            "precautions": assessment.precautions,
        }
        self.table.put_item(Item=item)
        return assessment

    def get_air_assessments(self, location_id: Optional[str] = None) -> List[AirAssessmentResponse]:
        if location_id:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"LOC#{location_id}",
                    ":sk_prefix": "AIR_ASSESSMENT#",
                },
            )
            items = response.get("Items", [])
        else:
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :gsi1pk",
                ExpressionAttributeValues={":gsi1pk": "ENTITY#AIR_ASSESSMENT"},
            )
            items = response.get("Items", [])

        results = []
        for it in items:
            it_clean = _decimal_to_float(it)
            results.append(
                AirAssessmentResponse(
                    assessment_id=it_clean["assessment_id"],
                    location_id=it_clean["location_id"],
                    timestamp=it_clean["timestamp"],
                    aqi=int(it_clean["aqi"]),
                    source=it_clean["source"],
                    dominant_pollutant=it_clean.get("dominant_pollutant"),
                    category=it_clean["category"],
                    risk_level=it_clean["risk_level"],
                    health_implications=it_clean["health_implications"],
                    precautions=it_clean.get("precautions", []),
                )
            )
        return results

    def save_waste_entry(self, entry: WasteEntry) -> WasteEntry:
        item = {
            "PK": f"LOC#{entry.location_id}",
            "SK": f"WASTE_ENTRY#{entry.timestamp.isoformat()}#{entry.entry_id}",
            "GSI1PK": "ENTITY#WASTE_ENTRY",
            "GSI1SK": entry.timestamp.isoformat(),
            "entity_type": "waste_entry",
            "entry_id": entry.entry_id,
            "location_id": entry.location_id,
            "timestamp": entry.timestamp.isoformat(),
            "category": entry.category,
            "quantity": _float_to_decimal(entry.quantity),
            "unit": entry.unit,
            "disposal_method": entry.disposal_method,
            "notes": entry.notes,
            "suggestion": entry.suggestion,
        }
        self.table.put_item(Item=item)
        return entry

    def get_waste_entries(self, location_id: Optional[str] = None) -> List[WasteEntry]:
        if location_id:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={
                    ":pk": f"LOC#{location_id}",
                    ":sk_prefix": "WASTE_ENTRY#",
                },
            )
            items = response.get("Items", [])
        else:
            response = self.table.query(
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :gsi1pk",
                ExpressionAttributeValues={":gsi1pk": "ENTITY#WASTE_ENTRY"},
            )
            items = response.get("Items", [])

        results = []
        for it in items:
            it_clean = _decimal_to_float(it)
            results.append(
                WasteEntry(
                    entry_id=it_clean["entry_id"],
                    location_id=it_clean["location_id"],
                    timestamp=it_clean["timestamp"],
                    category=it_clean["category"],
                    quantity=it_clean["quantity"],
                    unit=it_clean["unit"],
                    disposal_method=it_clean["disposal_method"],
                    notes=it_clean.get("notes"),
                    suggestion=it_clean["suggestion"],
                )
            )
        return results

    def clear_all(self) -> None:
        pass
