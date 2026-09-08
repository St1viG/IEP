FROM python:3

# First, and identical in all four dockerfiles, so Docker builds this layer once
# and the other three images reuse it from the cache. Keeping it above the source
# also means editing a service no longer reinstalls its dependencies.
COPY requirements.txt /requirements.txt
COPY wheels /wheels

# --no-index: install only from the wheels committed alongside the source, so the
# build needs no PyPI. Regenerate them with spakuj-wheels.sh after touching
# requirements.txt, or this fails loudly rather than silently reaching out.
RUN pip install --no-cache-dir --no-index --find-links /wheels -r ./requirements.txt

COPY src/configuration.py /configuration.py
COPY src/models.py /models.py
COPY src/validation.py /validation.py
COPY src/authentication.py /authentication.py

ENTRYPOINT [ "python", "authentication.py" ]
