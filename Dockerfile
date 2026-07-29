FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p static/uploads

# Expose the port Render will bind to
EXPOSE 10000

CMD ["gunicorn", "app:app", "--workers", "2", "--bind", "0.0.0.0:10000", "--timeout", "120"]
