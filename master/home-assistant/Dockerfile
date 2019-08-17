FROM homeassistant/home-assistant:0.97.1

RUN mkdir -p /certificates

VOLUME /config
VOLUME /letsencrypt

CMD [ "python", "-m", "homeassistant", "--config", "/config" ]
