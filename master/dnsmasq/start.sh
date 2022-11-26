#!/bin/sh

#echo "--- Starting arp scan ---"
#/sbin/ifconfig -a
#touch /etc/hosts.home
#arp-scan -l --interface eth0 -m /etc/hosts.home | head -n-3 | tail -n+3 | cut -f1,3-
echo "--- Starting dnsmasq ---"
webproc -u user --config /etc/config/dnsmasq.conf -- dnsmasq --no-daemon
