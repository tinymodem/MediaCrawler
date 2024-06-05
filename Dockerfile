FROM python:3.9
WORKDIR /crawler
COPY . /crawler
RUN pip install -r requirements.txt
RUN playwright install-deps
RUN playwright install