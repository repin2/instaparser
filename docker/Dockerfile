FROM python:3.11

COPY . /opt/app
WORKDIR /opt/app
RUN apt update -y
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt install  -y ./google-chrome-stable_current_amd64.deb

RUN apt install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
ENV PATH="$PATH:/usr/local/bin"

RUN pip install --no-cache-dir --upgrade -r /opt/app/requirements.txt
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
