#!/bin/bash

env DOCKER_BUILDKIT=1 docker build . -f Dockerfile.ops -t ops:latest
