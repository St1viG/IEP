FROM python:3

# The whole test suite in an image, so a machine with nothing but Docker can run
# it. The services it talks to are the ones deploy/development.yaml publishes on
# the host; deploy/testovi.sh points this at them.
COPY requirements-dev.txt /requirements-dev.txt
COPY requirements.txt /requirements.txt

RUN pip install -r ./requirements-dev.txt

COPY pytest.ini /pytest.ini
COPY src /src
COPY tests /tests
COPY contracts/output /contracts/output
COPY scenario.py /scenario.py

ENTRYPOINT [ "python", "-m", "pytest" ]
