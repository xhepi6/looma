FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8001

# Copy and set entrypoint
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Run the application
CMD ["./entrypoint.sh"]
