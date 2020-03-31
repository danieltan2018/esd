FROM python:3.7
EXPOSE 88
WORKDIR /WORKDIR
COPY requirements.txt /WORKDIR
RUN pip install -r requirements.txt
COPY user.py /WORKDIR
CMD python user.py