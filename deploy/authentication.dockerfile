FROM python:3

COPY src/configuration.py /configuration.py
COPY src/models.py /models.py
COPY src/validation.py /validation.py
COPY requirements.txt /requirements.txt
COPY src/authentication.py /authentication.py

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "authentication.py" ]
