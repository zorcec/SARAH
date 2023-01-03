#!/bin/sh

while true
do
        t=$(cat /sys/class/thermal/thermal_zone0/temp)
        t=$(($t/1000))

        echo CPU temp $t

        mosquitto_pub -h master_node -t tele/master_node/cpu_temperature -m "$t" 
        sleep 5
done