FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Change main.py to your actual starting file if it's different
CMD ["python", "main.py"]
