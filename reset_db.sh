#!/bin/bash

kubectl -n bugbounty scale --replicas=0 deployment/atst-beat
kubectl -n bugbounty scale --replicas=0 deployment/atst-worker
sleep 10
kubectl -n bugbounty exec $1 -c atst -- /opt/atat/atst/.venv/bin/python /opt/atat/atst/script/reset_database.py
sleep 2
kubectl -n bugbounty scale --replicas=1 deployment/atst-beat
kubectl -n bugbounty scale --replicas=1 deployment/atst-worker
