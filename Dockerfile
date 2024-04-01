FROM python:3.12
LABEL authors="David A. Mancilla"

# Create app directory
WORKDIR /server

# Install app dependencies
COPY ./requirements.txt ./
COPY ./swagger.yml ./
COPY ./.env ./

RUN pip install -r requirements.txt

# Bundle app source

COPY app /server/app

EXPOSE 8080
CMD [ "python", "/server/app/app.py" ]