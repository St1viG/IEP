FROM python:3

COPY requirements.txt /requirements.txt

RUN pip install -r ./requirements.txt

COPY src/configuration.py /configuration.py
COPY src/decorators.py /decorators.py
COPY src/validation.py /validation.py
COPY src/employee.py /employee.py

ENTRYPOINT [ "python", "employee.py" ]
