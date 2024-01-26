FROM homeassistant/home-assistant:2024.1.2

RUN mkdir -p /certificates

VOLUME /config
VOLUME /letsencrypt

CMD [ "python", "-m", "homeassistant", "--config", "/config" ]
