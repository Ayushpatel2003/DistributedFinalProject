FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY api /app/api
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
