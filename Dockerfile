FROM python:3.6.1-alpine
WORKDIR /CloudComputingA3-MySocialApp
ADD . /CloudComputingA3-MySocialApp

RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python","portal.py"]