import uuid
from datetime import datetime, timezone
from typing import Optional, List
from app.core.config import settings
from app.schemas.water import (
    WaterReadingCreate,
    WaterReading,
    WaterAssessmentRequest,
    WaterAssessmentResponse,
    WaterLeakReportCreate,
    WaterLeakReport,
    WaterSummaryResponse,
)


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class WaterService:
    def __init__(self, config=settings):
        self.config = config

    def assess_consumption(self, request: WaterAssessmentRequest) -> WaterAssessmentResponse:
        total_consumption = request.current_reading_liters - request.previous_reading_liters
        daily_usage = round(total_consumption / request.days_between, 2)
        usage_per_person = round(daily_usage / request.household_size, 2)
        
        has_baseline = (
            request.baseline_daily_per_person_liters is not None
            and request.baseline_daily_per_person_liters > 0
        )

        if has_baseline:
            baseline = request.baseline_daily_per_person_liters
            expected_total_daily = baseline * request.household_size
            excess = max(0.0, daily_usage - expected_total_daily)
            estimated_excess_liters = round(excess, 2)
            ratio = usage_per_person / baseline

            if ratio >= self.config.water_critical_ratio:
                status = "critical"
                severity = "critical"
                percent_over = round((ratio - 1.0) * 100, 1)
                explanation = (
                    f"Daily consumption of {usage_per_person:.1f} L/person is {percent_over}% above "
                    f"the baseline of {baseline:.1f} L/person. Unusual massive flow detected."
                )
                recommendation = (
                    "Possible major leak or continuous overflow. Shut off main supply valve "
                    "immediately and inspect primary pipes and water storage tanks."
                )
            elif ratio >= self.config.water_unusual_ratio:
                status = "unusual"
                severity = "high"
                percent_over = round((ratio - 1.0) * 100, 1)
                explanation = (
                    f"Daily consumption of {usage_per_person:.1f} L/person exceeds the baseline "
                    f"of {baseline:.1f} L/person by {percent_over}%."
                )
                recommendation = (
                    "Inspect taps, pipes, toilet flushes, and the water tank for suspected leaks "
                    "or unintended continuous flow."
                )
            elif ratio >= self.config.water_elevated_ratio:
                status = "elevated"
                severity = "medium"
                percent_over = round((ratio - 1.0) * 100, 1)
                explanation = (
                    f"Daily consumption of {usage_per_person:.1f} L/person is slightly elevated "
                    f"({percent_over}% above baseline of {baseline:.1f} L/person)."
                )
                recommendation = (
                    "Monitor meter readings over the next 24 to 48 hours to confirm if consumption "
                    "remains elevated or returns to normal."
                )
            else:
                status = "normal"
                severity = "low"
                explanation = (
                    f"Daily consumption of {usage_per_person:.1f} L/person is within the expected "
                    f"baseline range ({baseline:.1f} L/person)."
                )
                recommendation = "Consumption is within normal parameters. Continue standard monitoring."
        else:
            # When no baseline is supplied, do not fabricate excess water estimates
            estimated_excess_liters = 0.0
            benchmark = self.config.default_water_baseline_per_person_liters
            ratio = usage_per_person / benchmark

            if ratio >= self.config.water_unusual_ratio:
                status = "unusual"
                severity = "medium"
                explanation = (
                    f"Daily consumption of {usage_per_person:.1f} L/person is higher than standard "
                    f"regional benchmarks ({benchmark:.1f} L/person). Baseline not configured."
                )
                recommendation = (
                    "Inspect taps, pipes and the water tank. Set a household baseline to enable "
                    "precise excess calculation."
                )
            elif ratio >= self.config.water_elevated_ratio:
                status = "elevated"
                severity = "low"
                explanation = (
                    f"Daily consumption of {usage_per_person:.1f} L/person is slightly above standard "
                    f"benchmarks ({benchmark:.1f} L/person). Baseline not configured."
                )
                recommendation = "Check appliances and plumbing fixtures for minor drips."
            else:
                status = "normal"
                severity = "low"
                explanation = (
                    f"Daily consumption is {usage_per_person:.1f} L/person. No specific baseline was supplied."
                )
                recommendation = "Maintain regular meter logging to establish a reliable baseline."

        return WaterAssessmentResponse(
            assessment_id=f"w_assess_{uuid.uuid4().hex[:12]}",
            location_id=request.location_id,
            timestamp=datetime.now(timezone.utc),
            daily_usage_liters=daily_usage,
            usage_per_person_liters=usage_per_person,
            status=status,
            severity=severity,
            estimated_excess_liters=estimated_excess_liters,
            explanation=explanation,
            recommendation=recommendation,
        )

    def calculate_average_daily_usage(self, readings: List[WaterReading]) -> Optional[float]:
        if not readings:
            return None

        # Group readings by location_id
        by_location: dict[str, List[WaterReading]] = {}
        for r in readings:
            by_location.setdefault(r.location_id, []).append(r)

        location_averages: List[float] = []
        for loc_id, loc_readings in by_location.items():
            if len(loc_readings) < 2:
                continue
            # Sort by timestamp ensuring UTC-awareness
            sorted_readings = sorted(loc_readings, key=lambda r: _to_utc(r.timestamp))
            first = sorted_readings[0]
            last = sorted_readings[-1]

            time_diff = (_to_utc(last.timestamp) - _to_utc(first.timestamp)).total_seconds() / 86400.0
            if time_diff <= 0:
                continue

            consumption = last.cumulative_reading_liters - first.cumulative_reading_liters
            if consumption < 0:
                continue

            location_averages.append(consumption / time_diff)

        if not location_averages:
            return None

        # If single location was queried, return its average daily usage.
        # If multiple locations were queried, return the total daily usage across active locations.
        if len(by_location) == 1:
            return round(location_averages[0], 2)
        return round(sum(location_averages), 2)
