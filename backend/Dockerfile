FROM python:3.11-slim

# Install OS deps for psycopg/bcrypt
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Use pip wheel cache and install
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the backend source
COPY . /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
