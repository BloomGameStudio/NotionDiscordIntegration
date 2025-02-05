FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /bot

# Copy Pipfile and Pipfile.lock first for better caching
COPY Pipfile* ./

# Install pipenv and dependencies
RUN pip install pipenv && \
    pipenv install --deploy --system

# Copy source code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Use Python module path
CMD ["python", "-m", "src.main"]