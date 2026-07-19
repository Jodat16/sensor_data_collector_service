FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY run.py .

RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 5000

CMD ["gunicorn", "api:create_app()", "--bind", "0.0.0.0:5000"]
