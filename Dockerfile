FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8000
# TODO: implement the FastAPI backend in app.api.routes.chat before this container can run successfully.
CMD ["uvicorn", "app.api.routes.chat:app", "--host", "0.0.0.0", "--port", "8000"]
