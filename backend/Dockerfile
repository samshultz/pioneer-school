FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirement files
COPY requirements/base.txt /app/requirements/base.txt
COPY requirements/dev.txt /app/requirements/dev.txt
COPY requirements/prod.txt /app/requirements/prod.txt

# Install dependencies (choose one depending on environment)
RUN pip install --upgrade pip && pip install -r /app/requirements/base.txt


# Environment build arg
ARG DJANGO_ENV=production
ENV DJANGO_ENV=${DJANGO_ENV}

# Install dev requirements only in dev
RUN if [ "$DJANGO_ENV" = "development" ]; then pip install -r /app/requirements/dev.txt; fi

# Copy project code
COPY . .

# Expose port
EXPOSE 8000

# Collect static files
RUN python manage.py collectstatic --noinput

# Run with gunicorn
CMD ["gunicorn", "school_management.wsgi:application", "--bind", "0.0.0.0:8000"]
