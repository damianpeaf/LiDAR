FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY services/lidar-server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/lidar-server/main.py ./main.py

EXPOSE 3000

CMD ["python", "main.py"]
