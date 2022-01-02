FROM arm32v7/python:3.9-bullseye
RUN wget https://archive.raspbian.org/raspbian.public.key -O - | apt-key add - \
    && echo 'deb http://raspbian.raspberrypi.org/raspbian/ buster main contrib non-free rpi' | tee -a /etc/apt/sources.list \
    && wget -O - http://archive.raspberrypi.org/debian/raspberrypi.gpg.key | apt-key add - \
    && echo 'deb http://archive.raspberrypi.org/debian/ buster main ui' | tee -a /etc/apt/sources.list.d/raspi.list \
    && apt-get update \
    && apt-get install -y libatlas-base-dev libraspberrypi-bin \
    && mkdir /piplant
COPY static/pip.conf /etc/pip.conf
COPY requirements.txt requirements.txt
RUN python3 -m venv piplant-env && . piplant-env/bin/activate
RUN pip3 install --upgrade pip && python3 -m pip install -r requirements.txt --verbose

COPY . /piplant
CMD ["python3", "/piplant/piplant.py"]