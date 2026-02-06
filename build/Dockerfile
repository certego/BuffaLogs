FROM python:3.12-slim-trixie

ENV INSTALL_PATH /opt/certego
RUN mkdir -p $INSTALL_PATH
WORKDIR $INSTALL_PATH
COPY buffalogs/requirements.txt requirements.txt


RUN sed -i 's/main/main non-free/g' /etc/apt/sources.list.d/debian.sources \
 && apt-get update \
 && apt-get -y install \
    gcc \
    postgresql-client


RUN pip install --no-cache-dir -r requirements.txt \
    && rm -f requirements.txt && apt-get -y purge gcc && apt-get -y autoremove && apt-get -y clean


COPY buffalogs/ /opt/certego/buffalogs/
RUN chmod +x /opt/certego/buffalogs/run.sh; chmod +x /opt/certego/buffalogs/run_worker.sh; chmod +x /opt/certego/buffalogs/run_beat.sh;
WORKDIR /opt/certego/buffalogs/

CMD [ "./run.sh" ]
