FROM python:3.10-slim

# Install ffmpeg and required tools
RUN apt update && apt install -y ffmpeg curl && apt clean

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Launch the bot
CMD ["python", "main.py"]
