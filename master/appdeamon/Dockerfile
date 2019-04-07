FROM zorcec/base-debian-python3:latest

COPY /files/* /src/
RUN pip3 install --no-cache-dir -r /src/requirements_all.txt

# cleanup    
RUN apt-get clean

WORKDIR /src

VOLUME /src/apps

CMD ["appdaemon", "-c", "/src"]
