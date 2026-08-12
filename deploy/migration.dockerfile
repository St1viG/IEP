FROM python:3

COPY src/configuration.py /configuration.py
COPY src/models.py /models.py
COPY requirements.txt /requirements.txt
COPY src/migrate.py /migrate.py

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "migrate.py" ]
