# Use Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=backend.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development

# Run Flask
CMD ["flask", "run"]
