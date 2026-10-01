FROM python:3.12-slim

WORKDIR /app

ENV ACCEPT_EULA=Y
# Install Microsoft ODBC Driver 17 for SQL Server + build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends msodbcsql17 unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
    

COPY requirements.txt .

RUN  pip install -r requirements.txt

COPY . /app

EXPOSE 8501

CMD ["streamlit", "run", "sqlToWeb.py", "--server.port=8501", "--server.address=0.0.0.0"]
