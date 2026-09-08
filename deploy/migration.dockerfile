FROM python:3

COPY requirements.txt /requirements.txt
COPY wheels /wheels

# --no-index: install only from the wheels committed alongside the source, so the
# build needs no PyPI. Regenerate them with spakuj-wheels.sh after touching
# requirements.txt, or this fails loudly rather than silently reaching out.
RUN pip install --no-cache-dir --no-index --find-links /wheels -r ./requirements.txt

COPY src/configuration.py /configuration.py
COPY src/models.py /models.py
COPY src/migrate.py /migrate.py

ENTRYPOINT [ "python", "migrate.py" ]
