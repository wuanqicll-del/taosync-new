FROM node:18-alpine AS frontend-builder
WORKDIR /build
COPY frontend/ frontend/
RUN cd frontend && npm install && npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-builder /build/frontend/dist front/
EXPOSE 8023
CMD ["python", "main.py"]
