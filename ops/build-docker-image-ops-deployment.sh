#!/bin/bash

env IMAGE=cloudzeroopsregistry2.azurecr.io/rhel-py:latest DOCKER_BUILDKIT=1 docker build . -f ops.Dockerfile -t ops:jesse
