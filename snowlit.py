import streamlit as st
import pandas as pd
import plotly.express as px
import os
import duckdb

# Load AWS credentials from environment variables
minio_access_key = os.getenv("AWS_ACCESS_KEY_ID")
minio_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
minio_endpoint = os.getenv("MINIO_ENDPOINT")
bucket_name = "snow-data"

# Configure DuckDB with MinIO
duckdb.sql(f"""
    INSTALL httpfs;
    LOAD httpfs;
    SET s3_region='us-east-1';
    SET s3_url_style='path';
    SET s3_endpoint='{minio_endpoint}';
    SET s3_access_key_id='{minio_access_key}';
    SET s3_secret_access_key='{minio_secret_key}';
    SET s3_use_ssl=false;
""")


# Helper function to list available stations
def list_stations():
    query = f"""
    SELECT DISTINCT station_id FROM read_parquet('s3://{bucket_name}/wx_data/*/*.parquet')
    """
    stations = duckdb.query(query).df()["station_id"].tolist()
    return sorted(stations)


# helper function to load station data
def load_station_data(station_id):
    query = f"""
    SELECT date_time, air_temp_set_1
    FROM read_parquet('s3://{bucket_name}/wx_data/{station_id}/*.parquet')
    ORDER BY date_time
    """
    return duckdb.query(query).df()


# Streamlit app
st.title("Weather Station Temperature Viewer")

# Select station ID
station_id = st.selectbox("Select a Weather Station", options=list_stations())

if station_id:
    # Load data for the selected station
    with st.spinner("Loading data..."):
        data = load_station_data(station_id)

    if not data.empty:
        # Plot temperature over time
        fig = px.line(
            data,
            x="date_time",
            y="air_temp_set_1",
            title=f"Temperature Over Time - Station {station_id}",
        )
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Temperature (°C)")

        # Display the Plotly figure
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found for the selected station.")
else:
    st.info("Please select a weather station.")
