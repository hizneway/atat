FROM cloudzeropwdevregistry.azurecr.io/rhelubi:8.2

RUN yum update info \
    && yum install -y gcc libffi-devel make wget zlib-devel

RUN cd /usr/src \
    && wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz \
    && tar xzf Python-3.7.3.tgz \
    && cd Python-3.7.3 \
    && ./configure --enable-optimizations \
    && make install \
    && rm /usr/src/Python-3.7.3.tgz
