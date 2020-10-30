#!/bin/bash
for i in $(az group list --query "[? contains(name,'dryrun6')][].{name:name}" -o tsv); do
    echo "deleting ${i} . ."
    az group delete -n ${i} --yes --no-wait
done
