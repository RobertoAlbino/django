FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py migrate --run-syncdb

CMD ["python", "-m", "pytest", "tests/", "-v"]
