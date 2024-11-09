FROM python:3.12-slim

LABEL org.opencontainers.image.source=https://github.com/npelikan/snowlit

# Set working directory
WORKDIR /app

# Copy app code
COPY . .

# Install dependencies
RUN pip install -U uv
RUN uv pip install -n -r requirements.txt

# Expose the port Streamlit uses
EXPOSE 8501

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "app.py"]