# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary tools
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    yq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for YAML and JSON processing
RUN pip install --no-cache-dir \
    pyyaml \
    jsonschema

# Copy the current directory contents into the container at /app
COPY . /app

# Run a command to verify the installation
CMD ["python", "-c", "import yaml, json; print('YAML and JSON tools are ready!')"]
