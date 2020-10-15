FROM homeassistant/armhf-homeassistant:0.117.0.dev20201010

RUN mkdir -p /certificates

VOLUME /config
VOLUME /letsencrypt

CMD [ "python", "-m", "homeassistant", "--config", "/config" ]
