FROM python:3

RUN mkdir -p /opt/src/store/kupac
WORKDIR /opt/src/store/kupac

COPY store/applicationKupac.py ./applicationKupac.py
COPY store/configuration.py ./configuration.py
COPY store/models.py ./models.py
COPY store/requirements.txt ./requirements.txt
COPY store/rolePerm.py ./rolePerm.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/store"

ENTRYPOINT ["python", "./applicationKupac.py"]