# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container at /usr/src/app/
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
# This includes python-dotenv
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container at /usr/src/app/
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Copy the entrypoint script into the container
COPY entrypoint.sh /usr/src/app/entrypoint.sh

# Make the script executable
RUN chmod +x /usr/src/app/entrypoint.sh

# Set the script as the entrypoint
ENTRYPOINT ["/bin/sh", "/usr/src/app/entrypoint.sh"]
