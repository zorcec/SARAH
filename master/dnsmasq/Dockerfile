FROM alpine:latest

ARG HOSTUID=1000
ARG HOSTGID=1000

# webproc release settings
ENV WEBPROC_VERSION 0.2.2
ENV WEBPROC_URL https://github.com/jpillora/webproc/releases/download/0.2.2/webproc_linux_amd64.gz

RUN apk update && \
	apk add --no-cache --virtual .depends \
	git automake autoconf make gcc g++ libpcap-dev && \
	apk add libpcap && \
	git clone https://github.com/royhills/arp-scan.git && \
	cd arp-scan && \
	autoreconf --install && \
	./configure && \
	make && \
	make install && \
	apk del .depends

# fetch dnsmasq and webproc binary
RUN apk update \
	&& apk add --no-cache dnsmasq \
	&& apk add --no-cache --virtual .build-deps curl \
	&& curl -sL $WEBPROC_URL | gzip -d - > /usr/local/bin/webproc \
	&& chmod +x /usr/local/bin/webproc \
	&& apk del .build-deps

#configure dnsmasq
RUN mkdir -p /etc/default/
RUN echo -e "ENABLED=1\nIGNORE_RESOLVCONF=yes" > /etc/default/dnsmasq

COPY ./start.sh /start.sh
COPY ./etc/* /etc/

ENTRYPOINT ["sh", "/start.sh"]
