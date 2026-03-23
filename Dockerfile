FROM python:3.11-alpine

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app /app

CMD ["python", "main.py"]

