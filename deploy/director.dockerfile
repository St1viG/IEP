FROM python:3

COPY src/configuration.py /configuration.py
COPY src/decorators.py /decorators.py
COPY src/validation.py /validation.py
COPY requirements.txt /requirements.txt
COPY src/utilities.py /utilities.py
COPY src/director.py /director.py

# utilities.py resolves these relative to its own parent's parent, which is / here.
COPY contracts/output/Voting.abi /contracts/output/Voting.abi
COPY contracts/output/Voting.bin /contracts/output/Voting.bin

RUN pip install -r ./requirements.txt

ENTRYPOINT [ "python", "director.py" ]
