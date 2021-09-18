FROM python:3.7.4-slim

RUN apt-get update && apt-get install -y vim

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY script.py ./

CMD ["python", "script.py"]
