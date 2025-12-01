FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV FLAG="CSBC{3L3V3N_51GN4L_574710N_D3M0}"
EXPOSE 8000

CMD ["python", "server.py"]

