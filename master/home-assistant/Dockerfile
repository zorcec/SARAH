FROM homeassistant/home-assistant:2023.6

RUN mkdir -p /certificates

VOLUME /config
VOLUME /letsencrypt

CMD [ "python", "-m", "homeassistant", "--config", "/config" ]
