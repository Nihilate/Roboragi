FROM python:3.7.0-slim

ADD . /

RUN pip install -e .

CMD ["python","./roboragi/AnimePlanet.py"]