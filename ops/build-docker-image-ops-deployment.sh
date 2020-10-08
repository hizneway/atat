#!/bin/bash

env DOCKER_BUILDKIT=1 docker build . -f ops.Dockerfile -t ops:latest
