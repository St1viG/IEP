FROM python:3

COPY admin.py /admin.py
COPY configuration.py /configuration.py
COPY models.py /models.py
COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ENTRYPOINT [ "python", "admin.py" ]
