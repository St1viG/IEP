FROM python:3

COPY configuration.py /configuration.py
COPY models.py /models.py
COPY requirements.txt /requirements.txt
COPY migrate.py /migrate.py

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "migrate.py" ]
