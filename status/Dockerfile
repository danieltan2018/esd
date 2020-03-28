FROM python:3.7
EXPOSE 8002
WORKDIR /WORKDIR
COPY requirements.txt /WORKDIR
RUN pip install -r requirements.txt
COPY status.py /WORKDIR
CMD python status.py