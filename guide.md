# EcoPulse Testing & Usage Guide

This document outlines the steps to test, run, and interact with the EcoPulse backend locally.

## Prerequisites

Ensure you are using a Windows environment with the virtual environment configured.

1.  **Virtual Environment:**
    ```powershell
    # Navigate to project root
    cd D:\Kaufee\projects\EnvHacks

    # Activate virtual environment
    .\.venv\Scripts\Activate.ps1
    ```

## 1. Running Automated Tests

Execute all tests to verify the core domain logic and API implementation:

```powershell
.\.venv\Scripts\pytest.exe tests\
```

## 2. Starting the Local API Server

Start the development server:

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## 3. Interacting with the API

You can test the endpoints using PowerShell's `Invoke-RestMethod` or `curl`.

### Health Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```

### Water Endpoints
- **Assess Consumption:**
  ```powershell
  $body = @{
      location_id = "property_001"
      previous_reading_liters = 1000
      current_reading_liters = 1100
      days_between = 1
      household_size = 4
      baseline_daily_per_person_liters = 50
  } | ConvertTo-Json

  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/water/assessments" -Method Post -Body $body -ContentType "application/json"
  ```
- **Log Meter Reading:** `POST http://127.0.0.1:8000/api/v1/water/readings`
- **List Readings:** `GET http://127.0.0.1:8000/api/v1/water/readings?location_id=property_001`
- **Report Leak:** `POST http://127.0.0.1:8000/api/v1/water/reports`
- **Water Summary:** `GET http://127.0.0.1:8000/api/v1/water/summary?location_id=property_001`

### Air Endpoints
- **Classify AQI & Log Observation:**
  ```powershell
  $body = @{
      location_id = "LOC-001"
      aqi = 125
      source = "station_alpha"
      dominant_pollutant = "PM2.5"
  } | ConvertTo-Json

  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/air/assessments" -Method Post -Body $body -ContentType "application/json"
  ```
- **List Air Assessments:** `GET http://127.0.0.1:8000/api/v1/air/assessments?location_id=LOC-001`

### Waste Endpoints
- **Log Waste Entry:**
  ```powershell
  $body = @{
      location_id = "LOC-001"
      category = "plastic"
      quantity = 2.5
      unit = "kg"
      disposal_method = "recycling"
  } | ConvertTo-Json

  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/waste/entries" -Method Post -Body $body -ContentType "application/json"
  ```
- **List Waste Entries:** `GET http://127.0.0.1:8000/api/v1/waste/entries?location_id=LOC-001`
- **Waste Summary & Diversion Rate:** `GET http://127.0.0.1:8000/api/v1/waste/summary?location_id=LOC-001`

## 4. CLI Utilities & Dataset Seeding

- **Validate Sample Datasets:**
  ```powershell
  .\.venv\Scripts\python.exe scripts/validate_datasets.py
  ```
- **Seed Local Repository with Demo Data:**
  ```powershell
  .\.venv\Scripts\python.exe scripts/seed_local.py --reset
  ```

## Running with DynamoDB (Optional)

To run the backend configured for DynamoDB (this requires access to an AWS account and a table created using the provided `template.yaml`):

```powershell
# Set environment variables
$env:STORAGE_BACKEND="dynamodb"
$env:DYNAMODB_TABLE_NAME="EcoPulseTable"

# Start the server
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

*Note: Ensure your AWS credentials are configured in your environment (`aws configure`) before attempting to use the DynamoDB backend.*
