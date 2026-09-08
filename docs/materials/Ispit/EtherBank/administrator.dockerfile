FROM python:3

COPY configuration.py /configuration.py
COPY models.py /models.py
COPY utilities.py /utilities.py
COPY decorators.py /decorators.py
COPY requirements.txt /requirements.txt
COPY administrator_account.json /administrator_account.json
COPY output/Account.abi /output/Account.abi
COPY output/Account.bin /output/Account.bin
COPY administrator.py /administrator.py

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "administrator.py" ]
