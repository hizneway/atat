# Image source is provided using `--build-arg IMAGE=<some-image>`.
# This will typically be our RHEL Python image.
#
# --build-arg IMAGE=cloudzerodryrunregistry.azurecr.io/rhel-py
#
# https://docs.docker.com/engine/reference/commandline/build/#options
ARG IMAGE
ARG REDHAT_USERNAME
ARG REDHAT_PASSWORD

FROM $IMAGE as builder

ARG CDN_URL=/static/assets/
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
      unzip \
      util-linux \
      wget \
      zlib-devel

# Install the `Python.h` file for compiling certain libraries.
RUN dnf install python3-devel -y

# Install dependencies for python3-saml
RUN yum install -y \
      libxml2-devel \
      xmlsec1 \
      xmlsec1-openssl

# Install dev dependencies required to build the xmlsec dependency of python3-saml
# TODO(tomdds): Find proper gpg secured sources for both of these

#
#
# https://developers.redhat.com/articles/renew-your-red-hat-developer-program-subscription
RUN subscription-manager remove --all
RUN subscription-manager clean
RUN subscription-manager register --username $REDHAT_USERNAME --password $REDHAT_PASSWORD
RUN subscription-manager refresh
RUN subscription-manager attach --auto

# https://access.redhat.com/articles/4348511#enable
RUN subscription-manager repos --enable codeready-builder-for-rhel-8-x86_64-rpms

# https://man7.org/linux/man-pages/man1/yum-utils.1.html
RUN yum repolist
RUN yum install yum-utils -y
RUN yum install libtool-ltdl-devel -y
RUN yum install xmlsec1-devel -y

COPY . .
RUN pip3 install uwsgi poetry
RUN poetry install --no-root --no-dev

# Install yarn.
# https://linuxize.com/post/how-to-install-yarn-on-centos-8/
RUN dnf install @nodejs -y
RUN curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo
RUN rpm --import https://dl.yarnpkg.com/rpm/pubkey.gpg
RUN dnf install yarn -y

# Install app dependencies

RUN yarn install

RUN rm -rf ./static/fonts \
      && cp -rf ./node_modules/uswds/dist/fonts ./static/fonts \
      && yarn build-prod

## NEW IMAGE
FROM $IMAGE

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

RUN subscription-manager remove --all
RUN subscription-manager clean
RUN subscription-manager register --username $REDHAT_USERNAME --password $REDHAT_PASSWORD
RUN subscription-manager refresh
RUN subscription-manager attach --auto

# https://access.redhat.com/articles/4348511#enable
RUN subscription-manager repos --enable codeready-builder-for-rhel-8-x86_64-rpms

RUN yum install yum-utils -y
RUN yum install libtool-ltdl-devel -y
RUN yum install xmlsec1-devel -y

# Install postgresql client.
# https://www.postgresql.org/download/linux/redhat/
# TODO(heyzoos): WE NEED TO CHECK THE GPG KEY ASAP
# TODO(heyzoos): Copy the out of these from the first stage to the final image.
# RUN dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm
RUN dnf install @postgresql -y
# Install postgresql client library
# RUN yum install libpq.i686

# Install dependencies for python3-saml
RUN yum install -y \
      libxml2-devel \
      xmlsec1 \
      xmlsec1-openssl

# Install dev dependencies required to build the xmlsec dependency of python3-saml
# TODO(tomdds): Find proper gpg secured sources for both of these
# RUN yum install -y ftp://ftp.redhat.com/pub/redhat/rhel/rhel-8-beta/appstream/x86_64/Packages/libtool-ltdl-devel-2.4.6-25.el8.x86_64.rpm
# RUN yum install -y http://mirror.centos.org/centos/8/PowerTools/x86_64/os/Packages/xmlsec1-devel-1.2.25-4.el8.x86_64.rps
RUN yum install libtool-ltdl-devel -y
RUN yum install xmlsec1-devel -y

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
