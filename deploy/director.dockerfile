FROM python:3

COPY requirements.txt /requirements.txt
COPY wheels /wheels

# --no-index: install only from the wheels committed alongside the source, so the
# build needs no PyPI. Regenerate them with spakuj-wheels.sh after touching
# requirements.txt, or this fails loudly rather than silently reaching out.
RUN pip install --no-cache-dir --no-index --find-links /wheels -r ./requirements.txt

COPY src/configuration.py /configuration.py
COPY src/decorators.py /decorators.py
COPY src/validation.py /validation.py
COPY src/utilities.py /utilities.py
COPY src/director.py /director.py

# utilities.py resolves these relative to its own parent's parent, which is / here.
COPY contracts/output/Voting.abi /contracts/output/Voting.abi
COPY contracts/output/Voting.bin /contracts/output/Voting.bin

ENTRYPOINT [ "python", "director.py" ]
