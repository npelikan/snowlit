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

wx_stations = {
    "C99": "Canyons - 9990",
    "REY": "Reynolds Peak",
    "UTCDF": "Cardiff Trailhead",
    "PC056": "Brighton",
    "IFF": "Cardiff Peak",
    "PC064": "Albion Basin",
    "AMB": "Alta - Baldy",
    "HP": "Hidden Peak",
    "CDYBK": "Canyons - Daybreak",
    "LSL": "La Sal",
    "GOLDB": "Gold Basin",
    "NLPU1": "North Long Point (Abajos)",
}

snotel_sites = {
    "Brighton, UT": "366:UT:SNTL",
    "Mill D, UT": "628:UT:SNTL",
    "Snowbird, UT": "766:UT:SNTL",
    "Atwater Plot, UT": "1308:UT:SNTL",
    "Thaynes Canyon, UT": "814:UT:SNTL",
    "La Sal Mountain, UT": "572:UT:SNTL",
    "Gold Basin, UT": "1304:UT:SNTL",
    "Mt Pennell, UT": "1269:UT:SNTL",
    "Chepeta Lake, UT": "396:UT:SNTL",
    "Camp Jackson, UT": "383:UT:SNTL",
}

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


# helper function to load station data
def load_station_data(station_id):
    query = f"""
    SELECT date_time, air_temp_set_1
    FROM read_parquet('s3://{bucket_name}/wx_data/{station_id}/*.parquet')
    ORDER BY date_time
    """
    df = duckdb.query(query).df()
    df.air_temp_set_1 = (df.air_temp_set_1 * 9 / 5) + 32
    return df


# Helper function to load SNOTEL data
def load_snotel_data(snotel_id, sensor):
    query = f"""
    SELECT dateTime, {sensor}
    FROM read_parquet('s3://{bucket_name}/snotel_data/{snotel_id}/*.parquet')
    ORDER BY dateTime
    """
    return duckdb.query(query).df()


# Streamlit app
st.title("Weather Station Temperature Viewer")

tab1, tab2 = st.tabs(["Weather Stations", "SNOTEL Stations"])

# Select station ID

with tab1:
    st.header("Weather Station Temperature Viewer")
    station_id = st.selectbox(
        "Select a Weather Station", options=list(wx_stations.keys())
    )

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

# Tab for SNOTEL Stations
with tab2:
    st.header("SNOTEL Station Data Viewer")
    # Selector for SNOTEL data columns
    column_to_plot = st.selectbox(
        "Select Data to Plot",
        options=[
            "Temperature",
            "Snow Depth",
            "Snow-Water Equivalent",
        ],
    )

    # Map selector to column names
    column_map = {
        "Temperature": "TOBS",
        "Snow Depth": "SNWD",
        "Snow-Water Equivalent": "WTEQ",
    }
    selected_column = column_map[column_to_plot]

    snotel_name = st.selectbox(
        "Select a SNOTEL Station", options=list(snotel_sites.keys())
    )
    snotel_id = snotel_sites[snotel_name].replace(":", "_")

    with st.spinner("Loading data..."):
        snotel_data = load_snotel_data(snotel_id=snotel_id, sensor=selected_column)

    if not snotel_data.empty:
        fig = px.line(
            snotel_data,
            x="dateTime",
            y=selected_column,
            title=f"{column_to_plot}",
        )
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text=selected_column)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No SNOTEL data found.")
