FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Pipfile and Pipfile.lock first for better caching
COPY Pipfile* ./

# Install pipenv and dependencies
RUN pip install pipenv && \
    pipenv install --deploy --system

# Copy source code
COPY . .

# Use Python module path with updated src path
ENV PYTHONPATH=/app
CMD ["python", "-m", "src.main"]