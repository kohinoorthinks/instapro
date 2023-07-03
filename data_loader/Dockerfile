# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and CSV file to the container
COPY values.yaml /app/
COPY load_data.py /app/
COPY data/event_log.csv /app/data/

# Set the command to run the script
CMD ["python", "load_data.py"]
