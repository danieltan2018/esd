FROM python:3.7
WORKDIR /WORKDIR
COPY requirements.txt /WORKDIR
RUN pip install -r requirements.txt
COPY error_handling.py /WORKDIR
CMD python error_handling.py