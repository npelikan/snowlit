import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# Load AWS credentials from environment variables
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

# AWS S3 configuration
s3_bucket = "snow-data"
s3_client = boto3.client(
    "s3",
    endpoint_url=f'http://{os.getenv("MINIO_ENDPOINT")}',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
)


# Helper function to list available stations
def list_stations(bucket):
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix="wx_data/")
    stations = set()
    if "Contents" in response:
        for obj in response["Contents"]:
            parts = obj["Key"].split("/")
            if len(parts) >= 2:
                stations.add(parts[1])
    return sorted(stations)


# Function to read station data
def load_station_data(bucket, station_id):
    # List all files for the given station ID
    df = pd.read_parquet(
        f"s3://{s3_bucket}/wx_data/{station_id}/",
        storage_options={
            "endpoint_url": f"http://{os.getenv("MINIO_ENDPOINT")}",
            "key": aws_access_key,
            "secret": aws_secret_key,
            "client_kwargs": {
                # "endpoint_url": "https://127.0.0.1:9000",
                "verify": False,
            },
            "use_ssl": False,
        },
    )
    return df


# Streamlit app
st.title("Weather Station Temperature Viewer")

# Select station ID
station_id = st.selectbox("Select a Weather Station", options=list_stations(s3_bucket))

if station_id:
    # Load data for the selected station
    with st.spinner("Loading data..."):
        data = load_station_data(s3_bucket, station_id)

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
