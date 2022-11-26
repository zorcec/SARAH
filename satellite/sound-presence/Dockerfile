FROM zorcec/base-debian-python3:latest

RUN apt-get update && apt-get install -y python-tk ffmpeg libasound2-dev

COPY /src/requirements_all.txt /src/requirements_all.txt
COPY /src/lib /src/lib
RUN pip install --no-cache-dir -r /src/requirements_all.txt
RUN pip install --no-cache-dir -e /src/lib/pyAudioAnalysis

# Cleanup
RUN apt-get clean autoremove

RUN mkdir -p /src
VOLUME /src

WORKDIR /src

CMD ["python3", "sound_presence.py"]
