FROM python:3

COPY configuration.py /configuration.py
COPY main.py /main.py
COPY models.py /models.py
COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ENTRYPOINT [ "python", "/main.py" ]
