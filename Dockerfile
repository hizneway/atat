FROM cloudzeropwdevregistry.azurecr.io/rhel-py AS builder

ARG CSP
ARG CDN_URL=/static/assets/
ARG AZURE_ACCOUNT_NAME=atat
ENV TZ UTC

WORKDIR /install

RUN yum updateinfo && \
      yum install -y \
      curl \
      ca-certificates \
      git \
      gzip \
      libffi \
      nodejs \
      rsync \
      sudo \
      tar \
      util-linux \
      wget \
      zlib-devel

# Install the `Python.h` file for compiling certain libraries.
RUN dnf install python3-devel -y

# Install yarn.
# https://linuxize.com/post/how-to-install-yarn-on-centos-8/
RUN dnf install @nodejs -y
RUN curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo
RUN rpm --import https://dl.yarnpkg.com/rpm/pubkey.gpg
RUN dnf install yarn -y

COPY . .

# Install app dependencies
RUN ./script/write_dotenv \
      && pip3 install uwsgi poetry \ 
      # TODO: Remove this when this issue is resolved:
      # https://github.com/sdispater/pendulum/issues/454#issuecomment-605519477
      && pip3 install pendulum

RUN poetry env use python3.7

RUN poetry install --no-root --no-dev 

RUN yarn install

RUN rm -rf ./static/fonts \
      && cp -rf ./node_modules/uswds/dist/fonts ./static/fonts \
      && yarn build-prod

## NEW IMAGE
FROM cloudzeropwdevregistry.azurecr.io/rhel-py

### Very low chance of changing
###############################
# Overridable default config
# App directory is provided using `--build-arg APP_DIR=<app-dir>`.
ARG APP_DIR=/opt/atat/atst
# Git SHA is provided using `--build-arg GIT_SHA=<git-sha>`.
ARG GIT_SHA

# Environment variables
ENV APP_DIR "${APP_DIR}"
ENV GIT_SHA "${GIT_SHA}"

# Create application directory
RUN set -x ; \
      mkdir -p ${APP_DIR}

# Set working dir
WORKDIR ${APP_DIR}

# Make `groupadd` command available.
# https://stackoverflow.com/a/44834295
RUN yum install shadow-utils.x86_64 -y

# Create a system group `atat`.
# https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/deployment_guide/s2-groups-cl-tools
RUN groupadd --system -g 101 atat

# Create a system user `atst` and add them to the `atat` group.
# https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/deployment_guide/s2-users-cl-tools
RUN useradd --system atst -g atat

# TODO(heyzoos): Make this all work as part of the first stage.
# Get the latest GPG key for enterprise linux 8.
# https://yum.theforeman.org/
# RUN wget "https://yum.theforeman.org/releases/2.1/RPM-GPG-KEY-foreman"
# Import it into the rpm db
# RUN rpm --import RPM-GPG-KEY-foreman

# Install postgresql client.
# https://www.postgresql.org/download/linux/redhat/
# TODO(heyzoos): WE NEED TO CHECK THE GPG KEY ASAP
# TODO(heyzoos): Copy the out of these from the first stage to the final image.
RUN dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm --nogpgcheck
RUN dnf install postgresql10 -y

# Install dumb-init.
# dumb-init is a simple process supervisor and init system designed to run as PID 1 inside minimal container environments.
RUN pip3 install dumb-init

# Install the `Python.h` file for compiling certain libraries.
RUN dnf install python3-devel -y

# Install uwsgi.
# Logfile plugin is embedded by default.
# https://uwsgi-docs.readthedocs.io/en/latest/Logging.html#logging-to-files
RUN pip3 install uwsgi pendulum

COPY . .

COPY --from=builder /install/.venv/ ./.venv/
COPY --from=builder /install/alembic/ ./alembic/
COPY --from=builder /install/alembic.ini .
COPY --from=builder /install/app.py .
COPY --from=builder /install/atat/ ./atat/
COPY --from=builder /install/celery_worker.py ./celery_worker.py
COPY --from=builder /install/config/ ./config/
COPY --from=builder /install/policies/ ./policies/
COPY --from=builder /install/templates/ ./templates/
COPY --from=builder /install/translations.yaml .
COPY --from=builder /install/script/ ./script/
COPY --from=builder /install/static/ ./static/
COPY --from=builder /install/fixtures/ ./fixtures
COPY --from=builder /install/uwsgi.ini .
COPY --from=builder /usr/local/bin/uwsgi /usr/local/bin/uwsgi

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Default command is to launch the server
CMD ["uwsgi", "--ini", "uwsgi.ini"]

RUN mkdir /var/run/uwsgi && \
      chown -R atst:atat /var/run/uwsgi && \
      chown -R atst:atat "${APP_DIR}"

RUN update-ca-trust

# Run as the unprivileged APP user
USER atst
