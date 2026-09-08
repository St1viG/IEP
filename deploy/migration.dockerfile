FROM python:3

COPY requirements.txt /requirements.txt

RUN pip install -r ./requirements.txt

COPY src/configuration.py /configuration.py
COPY src/models.py /models.py
COPY src/migrate.py /migrate.py

ENTRYPOINT [ "python", "migrate.py" ]
