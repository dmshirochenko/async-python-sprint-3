# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
  iputils-ping \
  && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container at /usr/src/app/
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
# This includes python-dotenv
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container at /usr/src/app/
COPY . .

# Run ping to check reachability before running pytest
CMD ["sh", "-c", "ping -c 5 my-python-server && pytest"]
