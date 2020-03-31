FROM python:3.7
EXPOSE 80
WORKDIR /WORKDIR
COPY requirements.txt /WORKDIR
RUN pip install -r requirements.txt
COPY monitoring.py /WORKDIR
CMD python status.py