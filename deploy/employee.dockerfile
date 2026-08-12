FROM python:3

COPY src/configuration.py /configuration.py
COPY src/decorators.py /decorators.py
COPY src/validation.py /validation.py
COPY requirements.txt /requirements.txt
COPY src/employee.py /employee.py

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "employee.py" ]
