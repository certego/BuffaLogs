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

# Fix line endings and set execute permissions
RUN apt-get update && apt-get install -y dos2unix \
    && dos2unix /opt/certego/buffalogs/run.sh /opt/certego/buffalogs/run_worker.sh /opt/certego/buffalogs/run_beat.sh \
    && chmod +x /opt/certego/buffalogs/run.sh /opt/certego/buffalogs/run_worker.sh /opt/certego/buffalogs/run_beat.sh \
    && apt-get -y purge dos2unix && apt-get -y autoremove && apt-get -y clean

WORKDIR /opt/certego/buffalogs/

CMD ["/bin/bash", "/opt/certego/buffalogs/run.sh"]
