# Notion/Discord Integration

<div align="center">

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://docs.docker.com/compose/install/)

</div>

A Discord bot that integrates with Notion for updates and notifications.

## Setup
Make copy of the environment variables file and fill in appropriate values:
```bash
cp .env.example .env
```

## Run

### Docker (recommended)
1. Ensure [Docker](https://docs.docker.com/compose/install/) is installed.
2. Start the containers:
```bash
docker compose up
```

### Local Heroku

1. Ensure [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) is installed.
2. Install dependencies:
```bash
pipenv install --dev
```
3. Run the bot:
```bash
heroku local
```

## Run Scripts
**Double check your environment variables are set to target the correct database.**

Activate the virtual environment:
```bash
pipenv shell
```

### Initialize database
```bash
python -m src.scripts.init_db
```

### Run query
```bash
python -m src.scripts.query
```
