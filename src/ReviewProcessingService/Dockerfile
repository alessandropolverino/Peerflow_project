FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install --no-cache-dir pytest pytest-cov pytest-watch

COPY ./src/ /app/src/

EXPOSE 3000

# Run the application with reload enabled
CMD ["fastapi", "dev", "/app/src/app.py", "--port", "3000", "--host", "0.0.0.0"]