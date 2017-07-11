# https://phusion.github.io/baseimage-docker/
FROM phusion/baseimage:0.9.22

RUN apt-get update
RUN apt-get install -y build-essential git curl python python-dev libffi-dev libssl-dev python-pip unzip redis-server
RUN pip install -U pip

ADD requirements.txt /code/funnel/requirements.txt
RUN pip install -r /code/funnel/requirements.txt
RUN cd /usr/local/lib/python2.7/dist-packages/baseframe && make

ADD . /code/funnel

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 3000

CMD ["python", "/code/funnel/runserver.py"]
