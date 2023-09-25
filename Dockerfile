FROM madiva/python:latest

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip &&\
    pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY components/* ./components/
COPY services/* ./services/


COPY images/logo.png ./images/
COPY secrets.toml.template .streamlit/secrets.toml


EXPOSE 8501
ENV BUCKET_NAME=__NO_BUCKET__
CMD streamlit run datalakeStudio.py -- $BUCKET_NAME
