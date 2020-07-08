# Image source is provided using `--build-arg IMAGE=<some-image>`.
# https://docs.docker.com/engine/reference/commandline/build/#options
ARG IMAGE

FROM $IMAGE

# Removes the specified packages from the system along with any
# packages depending on the packages being removed.
# https://man7.org/linux/man-pages/man8/yum.8.html
RUN yum remove python3

# Removes all “leaf” packages from the system that were originally
# installed as dependencies of user-installed packages, but which
# are no longer required by any such package.
# https://man7.org/linux/man-pages/man8/yum.8.html
RUN yum autoremove python3

# Update package repository information.
# http://man7.org/linux/man-pages/man8/yum.8.html
RUN yum updateinfo

# Upgrade all packages with their latest security updates.
# http://man7.org/linux/man-pages/man8/yum.8.html
RUN yum upgrade --security

# Necessary for building python.
RUN yum install -y gcc libffi-devel make wget zlib-devel

# Causes python to be built with SSL capabilitiy, allowing pip to function.
RUN yum install -y openssl-devel

# Need EPEL to install SQLLite
# https://fedoraproject.org/wiki/EPEL
# TODO(heyzoos): Do the GPG check.
RUN yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm --nogpgcheck

# Allows python to use SQLLite modules.
RUN yum install -y sqlite sqlite-devel libsqlite3x.x86_64

# Install python!
# https://github.com/python/cpython#build-instructions
RUN cd /usr/src \
    && wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz \
    && tar xzf Python-3.7.3.tgz \
    && cd Python-3.7.3 \
    && ./configure --enable-loadable-sqlite-extensions --enable-optimizations \
    && make install \
    && rm /usr/src/Python-3.7.3.tgz
