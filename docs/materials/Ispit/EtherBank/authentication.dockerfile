FROM python:3

COPY configuration.py /configuration.py
COPY models.py /models.py
COPY utilities.py /utilities.py
COPY requirements.txt /requirements.txt
COPY authentication.py /authentication.py

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "authentication.py" ]
