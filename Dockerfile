FROM python:3.13.7-slim

WORKDIR /app

# Capture build information during build
ARG GIT_COMMIT_HASH
ARG GIT_COMMIT_MESSAGE
ARG GIT_COMMIT_DATE
ARG GIT_BRANCH

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files (excluding .git directory)
COPY app.py .
COPY . .

# Generate build_info.py with git information baked into the code
RUN echo "# Auto-generated build information - DO NOT EDIT" > build_info.py && \
    echo "BUILD_COMMIT_HASH = '${GIT_COMMIT_HASH:-unknown}'" >> build_info.py && \
    echo "BUILD_COMMIT_MESSAGE = '${GIT_COMMIT_MESSAGE:-unknown}'" >> build_info.py && \
    echo "BUILD_COMMIT_DATE = '${GIT_COMMIT_DATE:-unknown}'" >> build_info.py && \
    echo "BUILD_BRANCH = '${GIT_BRANCH:-unknown}'" >> build_info.py

# Remove any .git directory that might have been copied
RUN rm -rf .git

# Install system dependencies (removed git as we don't need it in container)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and switch to it
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

 