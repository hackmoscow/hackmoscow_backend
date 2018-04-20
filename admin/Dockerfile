FROM python:3.6-alpine
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

COPY requirements.txt /src/requirements.txt
RUN pip install -U --user -r /src/requirements.txt

ENV PYTHONPATH=/src

#COPY setup.py /src/setup.py
#RUN pip install --no-cache-dir -r /src/setup.py

COPY . /src
RUN python /src/setup.py develop

EXPOSE 8000

CMD ["run_admin"]