FROM python:3.6-slim

# Install the tools we need.
RUN apt-get update && apt-get install -y git
RUN pip install pipenv

# Set working directory
WORKDIR /app

# Install project dependencies.
ADD Pipfile.lock /app
ADD Pipfile /app
RUN pipenv sync --dev

# Copy the rest of the project
ADD . /app

# Run tests
CMD pipenv run python -m pytest --doctest-modules --junitxml=test_results.xml
