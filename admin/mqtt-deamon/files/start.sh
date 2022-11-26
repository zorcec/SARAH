echo "Cleaning logs!"
rm -rf /files/mqtt-spy-daemon.log
rm -rf /files/mqtt-spy-daemon.messages
touch /files/mqtt-spy-daemon.log
touch /files/mqtt-spy-daemon.messages

echo "Starting deamon"
java -jar mqtt-spy-daemon-0.2.0-beta-b1-jar-with-dependencies.jar /config/config.xml