FROM python:3

COPY configuration.py /configuration.py
COPY models.py /models.py
COPY migrate.py /migrate.py
COPY migrate.sh /migrate.sh
COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ENTRYPOINT [ "sh", "/migrate.sh" ]
