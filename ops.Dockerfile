FROM cloudzeroopsregistry.azurecr.io/rhel-py:latest

COPY ./azure-cli.repo /etc/yum.repos.d/azure-cli.repo




COPY ./ops/requirements.txt /src/ops/requirements.txt

RUN pip3 install -r /src/ops/requirements.txt

COPY . /src

WORKDIR /src/ansible

ENTRYPOINT ["../ops/entrypoint.sh"]
