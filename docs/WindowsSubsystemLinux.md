# Configuring Windows Subsystem for Linux to run the local server

These instructions cover setting up the local server on Windows Subsystem for
Linux, specifically focusing on Ubuntu 20.04. For instructions on initial
installation and configuration of the Windows Subsystem for Linux, consult
the [Microsoft Documentation](https://docs.microsoft.com/en-us/windows/wsl/install-win10).

## Updating packages

If you are using a fresh WSL installation, don't forget to update your package
cache and update all installed packages.

```
# apt update
# apt upgrade
```

## Install prerequisites

Some prerequisites need to be installed prior to the following steps:

```
# apt install git python3 python-is-python3
```

## Python Setup

Currently, ATAT requires specifically Python 3.7.3. Since Ubuntu currently
includes Python 3.8 in the repositories, Python 3.7.3 must be installed through
external means. This can be done with [`pyenv`](https://github.com/pyenv/pyenv).

1. Install the [prerequisites](https://github.com/pyenv/pyenv/wiki#suggested-build-environment)
   for building Python
1. Checkout `pyenv`
   ```
   $ git clone https://github.com/pyenv/pyenv.git ~/.pyenv
   ```
1. Add `pyenv` to `~/.bashrc`:
   ```
    $ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    $ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    $ echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc
    ```
1. Install Python 3.7.3: `pyenv install 3.7.3`

If you get an error that `pyenv` is not installed, re-execute your shell by
running the following and trying again:

```
$ exec "$SHELL"
```

Temporarily enter the `pyenv` environment for Python 3.7.3 and install Poetry:

```
$ pyenv shell 3.7.3
$ pip install poetry 
```

## Package Installation

All of Redis, NodeJS, Yarn, `xmlsec1`, and PostgreSQL are available through the
Ubuntu repositories and can be installed with:

```
# apt install redis nodejs postgresql yarnpkg xmlsec1
```

## Configuring `yarn`

Since Ubuntu and associated Linux distributions call `yarn` as `yarnpkg`,
it will be necessary to symlink `yarnpkg` as `yarn`:

```
# ln -s "$(which yarnpkg)" /usr/local/bin/yarn
```

## Starting Services

Despite the package being installed, systemd does not work under WSL and there
is not currently support for automatically starting services. The `redis-server`
and `postgresql` services will need to be started manually with:

```
# service redis-server start
# service postgresql start
```

## Setting PostgreSQL password

If you were not prompted to do so, it will be necessary to set the password
for the `postgres` user. This value is configured in
[config/base.ini](/config/base.ini) and by default, the expected value is
`postgres`.

The password can be set by switching to the `postgres` Unix user:

```
# su postgres
```

Then connecting the PostgreSQL server started above:

```
$ psql
```

At this point, the password can be set with the following SQL statement,
specifying the appropriate password and updating the configuration as needed:

```
postgres=# ALTER USER postgres WITH PASSWORD 'password';
postgres=# exit
```

Then `exit` to return to your user within WSL.

## Proceed with setup and running

Ensure you are using the Python 3.7.3 installed earlier by running

```
pyenv shell 3.7.3
```

From here, your local development environment should be sufficiently configured
to proceed with the [setup](https://github.com/dod-ccpo/atst#setup) section of
the README and to continue with running the local development server.