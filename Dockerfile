FROM anasty17/mltb:latest

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

RUN python3 -m venv venv

COPY requirements.txt .
RUN venv/bin/pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash", "start.sh"]