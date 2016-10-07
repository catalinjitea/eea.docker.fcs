FROM python:2.7-slim
MAINTAINER "EEA: IDM2 C-TEAM" <eea-edw-c-team-alerts@googlegroups.com>

ENV WORK_DIR=/var/local/fcs

RUN runDeps="curl vim build-essential netcat libpq-dev" \
 && apt-get update \
 && apt-get install -y --no-install-recommends $runDeps \
 && rm -vrf /var/lib/apt/lists/*

COPY . $WORK_DIR/
WORKDIR $WORK_DIR

RUN pip install -r requirements-dep.txt \
 && mv docker-entrypoint.sh /bin/

ENTRYPOINT ["docker-entrypoint.sh"]