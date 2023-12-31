FROM python:3.10

# Install pipenv and compilation dependencies
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc

WORKDIR /bot

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --deploy 


# Install application into container
COPY . .

# Run the application
CMD pipenv run python bot.py
# CMD ["pipenv", "run", "python", "bot.py"]