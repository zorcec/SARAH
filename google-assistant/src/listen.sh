
echo "Starting assistant..."
googlesamples-assistant-hotword --project_id sarah-f0a98 --device_model_id docker

echo "Cannot start... Starting SSH"
/usr/sbin/sshd -D
