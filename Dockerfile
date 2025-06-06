FROM python:3.13-slim

WORKDIR /app

# Capture git information during build (before copying source)
ARG GIT_COMMIT_HASH
ARG GIT_COMMIT_MESSAGE
ARG GIT_COMMIT_DATE
ARG GIT_BRANCH

# Set git info as environment variables early
ENV GIT_COMMIT_HASH=${GIT_COMMIT_HASH:-unknown}
ENV GIT_COMMIT_MESSAGE=${GIT_COMMIT_MESSAGE:-unknown}
ENV GIT_COMMIT_DATE=${GIT_COMMIT_DATE:-unknown}
ENV GIT_BRANCH=${GIT_BRANCH:-unknown}

# Debug: Show what build args were received
RUN echo "=== Docker Build Debug Information ===" && \
    echo "GIT_COMMIT_HASH: ${GIT_COMMIT_HASH}" && \
    echo "GIT_COMMIT_MESSAGE: ${GIT_COMMIT_MESSAGE}" && \
    echo "GIT_COMMIT_DATE: ${GIT_COMMIT_DATE}" && \
    echo "GIT_BRANCH: ${GIT_BRANCH}" && \
    echo "========================================="

# Install system dependencies (removed git as we don't need it in container)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files (excluding .git directory)
COPY app.py .
COPY . .

# Remove any .git directory that might have been copied
RUN rm -rf .git

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

 