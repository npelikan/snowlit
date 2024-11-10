# api.py
import os
import duckdb
import strawberry
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException, status
from strawberry.fastapi import GraphQLRouter
import datetime

# Load API key from environment variables
API_KEY = os.getenv("API_KEY", "your_default_api_key")  # Replace with actual API key

# Load MinIO credentials from environment variables
minio_access_key = os.getenv("AWS_ACCESS_KEY_ID")
minio_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
minio_endpoint = os.getenv("MINIO_ENDPOINT")
bucket_name = "snow-data"

# Configure DuckDB with MinIO
duckdb.sql(f"""
    INSTALL httpfs;
    LOAD httpfs;
    SET s3_endpoint='{minio_endpoint}';
    SET s3_access_key_id='{minio_access_key}';
    SET s3_secret_access_key='{minio_secret_key}';
    SET s3_use_ssl=false;
""")


# Define Strawberry GraphQL types
@strawberry.type
class WeatherStationData:
    date_time: datetime.datetime
    tobs: Optional[float] = None


# define weather station column renames. This is in format stored_colname:
weather_station_renames = {"air_temp_set_1": "tobs"}


@strawberry.type
class SnotelData:
    date_time: datetime.datetime
    tobs: Optional[float] = None
    snwd: Optional[float] = None
    wteq: Optional[float] = None


@strawberry.type
class Query:
    @strawberry.field
    def weather_station_data(
        self, station_id: str, sensors: List[str] = ["tobs"]
    ) -> List[WeatherStationData]:
        selected_sensors = [
            f"{k} AS {v}" for k, v in weather_station_renames.items() if v in sensors
        ]
        query = f"""
        SELECT date_time, {selected_sensors.join(", ")}
        FROM read_parquet('s3://{bucket_name}/wx_data/{station_id}/*.parquet')
        ORDER BY date_time
        """
        result = duckdb.query(query).to_df()
        return [
            WeatherStationData(
                date=row["date"],
                tobs=row.get("tobs") if "tobs" in sensors else None,
            )
            for _, row in result.iterrows()
        ]

    @strawberry.field
    def snotel_data(
        self, station_id: str, sensors: List[str] = ["tobs", "snwd", "wteq"]
    ) -> List[SnotelData]:
        sensor_fields = ", ".join(sensors)
        query = f"""
        SELECT dateTime as date_time, {sensor_fields}
        FROM read_parquet('s3://{bucket_name}/snotel_data/{station_id}/*.parquet')
        ORDER BY dateTime
        """
        result = duckdb.query(query).to_df()
        return [
            SnotelData(
                date_time=row["date_time"],
                tobs=row.get("TOBS") if "TOBS" in sensors else None,
                snwd=row.get("SNWD") if "SNWD" in sensors else None,
                wteq=row.get("WTEQ") if "WTEQ" in sensors else None,
            )
            for _, row in result.iterrows()
        ]


# Initialize FastAPI app and add API key authentication
app = FastAPI()


# Middleware for API Key validation
@app.middleware("http")
async def check_api_key(request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    response = await call_next(request)
    return response


# Create a GraphQL schema with Strawberry
schema = strawberry.Schema(query=Query)

# Add GraphQL endpoint to FastAPI app
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
