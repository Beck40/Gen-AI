FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your project folders into the container
COPY code/ /app/code/
COPY data/ /app/data/
COPY docs/ /app/docs/

# Set Environment Variables
# Ensures Python knows where to look for your modules
ENV PYTHONPATH="/app/code"
# Ensures logs print immediately (crucial for debugging in AWS/Docker)
ENV PYTHONUNBUFFERED=1

# The Start Command
CMD ["python", "code/docker/analyst.py"]
