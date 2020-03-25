FROM python:3.7
EXPOSE 8002
COPY requirements.txt /app
WORKDIR /app
RUN pip install -r requirements.txt
COPY status.py /app
CMD python status.py