FROM python:3.8

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip &&\
    pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY images/logo.png ./images/
COPY secrets.toml.template .streamlit/secrets.toml

EXPOSE 8501

CMD streamlit run datalakeStudio.py
