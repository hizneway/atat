#!/bin/bash -x
#
# adapted from https://stackoverflow.com/a/40530391
#
# make-chain.sh:
# 1. creates a root CA and an intermediate CA signed by the root
# 2. creates a client cert signed by the intermediate
# 3. creates a CRL with no revocations
# 4. concatenates the root and intermediate certs into a chain
# 5. cleans up anything we don't need for testing

set -e

for C in `echo root-ca intermediate`; do

  mkdir $C
  cd $C
  cd ..

  echo 1000 > $C/serial
  touch $C/index.txt $C/index.txt.attr

  echo '
[ ca ]
default_ca = CA_default
[ CA_default ]
dir            = '$C'    # Where everything is kept
certs          = $dir # Where the issued certs are kept
crl_dir        = $dir                # Where the issued crl are kept
database       = $dir/index.txt            # database index file.
new_certs_dir  = $dir            # default place for new certs.
certificate    = $dir/cacert.pem                # The CA certificate
serial         = $dir/serial                # The current serial number
crl            = $dir/crl.pem                # The current CRL
private_key    = $dir/ca.key.pem       # The private key
RANDFILE       = $dir/.rnd     # private random number file
nameopt        = default_ca
certopt        = default_ca
policy         = policy_match
default_days   = 3650
default_md     = sha256
default_crl_days = 3650

[ policy_match ]
countryName            = optional
stateOrProvinceName    = optional
organizationName       = optional
organizationalUnitName = optional
commonName             = supplied
emailAddress           = optional

[req]
req_extensions = v3_req
distinguished_name = req_distinguished_name

[req_distinguished_name]

[v3_req]
basicConstraints = CA:TRUE
' > $C/openssl.conf
done

openssl genrsa -out root-ca/ca.key 2048
openssl req -config root-ca/openssl.conf -new -x509 -days 3650 -key root-ca/ca.key -sha256 -extensions v3_req -out root-ca/ca.crt -subj '/CN=Root-ca'

openssl genrsa -out intermediate/intermediate.key 2048
openssl req -config intermediate/openssl.conf -sha256 -new -days 3650 -key intermediate/intermediate.key -out intermediate/intermediate.csr -subj '/CN=Interm.'
openssl ca -batch -config root-ca/openssl.conf -keyfile root-ca/ca.key -cert root-ca/ca.crt -extensions v3_req -notext -md sha256 -in intermediate/intermediate.csr -out intermediate/intermediate.crt

openssl req -new -keyout client.key -out client.request -days 3650 -nodes -subj "/CN=client.example.com" -newkey rsa:2048
openssl ca -batch -config root-ca/openssl.conf -keyfile intermediate/intermediate.key -cert intermediate/intermediate.crt -out client.crt -infiles client.request

openssl ca -gencrl -keyfile intermediate/intermediate.key -crldays 3649 -cert intermediate/intermediate.crt -out intermediate.pem.crl -config intermediate/openssl.conf
openssl crl -inform pem -outform der -in intermediate.pem.crl -out intermediate.crl

cat intermediate/intermediate.crt root-ca/ca.crt >> ca-chain.pem
rm -r client.key client.request intermediate.pem.crl intermediate/ root-ca/
