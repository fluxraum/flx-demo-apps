# Deployed via the platform's "streamlit" hosting template (see
# templates/streamlit/) -- a standard `streamlit run` entrypoint is what
# lets that chart's STREAMLIT_SERVER_BASE_URL_PATH env var (set from
# ingress.path) work without the chart needing to know anything about
# this specific app.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
