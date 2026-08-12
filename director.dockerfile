FROM python:3

COPY configuration.py /configuration.py
COPY decorators.py /decorators.py
COPY validation.py /validation.py
COPY requirements.txt /requirements.txt
COPY director.py /director.py

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "director.py" ]
