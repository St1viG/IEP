FROM python:3

COPY requirements.txt /requirements.txt
COPY wheels /wheels

# From PyPI by default. To build with no network at all, fill wheels/ with
# spakuj-wheels.sh and pass:
#   --build-arg PIP_ARGS="--no-index --find-links /wheels"
# The submitted archive ships without wheels/, which is why this cannot be the
# default: there it has to reach PyPI like any other project.
ARG PIP_ARGS=""

RUN pip install --no-cache-dir ${PIP_ARGS} -r ./requirements.txt

COPY src/configuration.py /configuration.py
COPY src/decorators.py /decorators.py
COPY src/validation.py /validation.py
COPY src/employee.py /employee.py

ENTRYPOINT [ "python", "employee.py" ]
