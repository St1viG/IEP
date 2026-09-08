# Ubuntu OS + python3
FROM python:3

# create a directory for the application
RUN mkdir /flask_application

# change working directory
WORKDIR /flask_application

# copy relevant files
COPY configuration.py ./configuration.py
COPY decorators.py ./decorators.py
COPY models.py ./models.py
COPY main.py ./main.py
COPY requirements.txt ./requirements.txt

# install all necessary modules
RUN pip install -r ./requirements.txt

# python main.py
ENTRYPOINT [ "python", "main.py" ]
