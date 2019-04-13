FROM zorcec/base-debian-python3:latest

RUN apt-get update && apt-get install -y openssh-server portaudio19-dev libffi-dev libssl-dev libmpg123-dev python3-openssl

COPY /src/ /src
RUN pip install --no-cache-dir -r /src/requirements_all.txt

RUN mkdir /var/run/sshd
RUN echo 'root:root' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

# Cleanup
RUN apt-get clean autoremove

RUN mkdir -p /src
VOLUME /src

WORKDIR /src

EXPOSE 22

CMD ["bash", "listen.sh"]
