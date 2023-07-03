# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script and CSV file to the container
COPY values.yaml /app/
COPY model_data.py /app/

# Set the command to run the script
CMD ["python", "model_data.py"]
