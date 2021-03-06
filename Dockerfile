FROM latonaio/l4t:latest

# Definition of a Device & Service
ENV POSITION=Runtime \
    SERVICE=check-usb-storage-connection\
    AION_HOME=/var/lib/aion
RUN mkdir ${AION_HOME}
WORKDIR ${AION_HOME}
# Setup Directoties
RUN mkdir -p \
    $POSITION/$SERVICE
WORKDIR ${AION_HOME}/$POSITION/$SERVICE/
RUN apt update -y  && apt install -y exfat-fuse exfat-utils ntfs-3g
ADD . .

RUN python3 setup.py install

# CMD ["python3", "-u", "main.py"]
CMD ["/bin/sh", "docker-entrypoint.sh"]
