FROM resin/raspberry-pi-python:2.7-slim
RUN pip install -U pip
RUN pip install influxdb
RUN pip install flask
#Move this to different docker file for just sending info to server
RUN pip install psutil
RUN pip install flatten_json
#I doubt this is needed
RUN sudo apt-get install python-dev
EXPOSE 5000
COPY . /app
WORKDIR /app
CMD ["python", "pi_mgmt.py"]
