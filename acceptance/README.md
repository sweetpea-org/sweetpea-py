Acceptance Tests
================

This directory contains end-to-end tests that can be run to ensure we don't introduce any regressions when we need to make changes to the encoding.

Execute the tests with `make acceptance`.

To make them run faster, start the backend docker container yourself, and then export `SWEETPEA_EXTERNAL_DOCKER_MGMT=true` in your shell to tell `sweetpea` that you're managing the container yourself:

```
➜  sweetpea-py git:(master) ✗ docker run -d -p 8080:8080 sweetpea/server 
30c3576d311d23899fee96a7a2c12ef74502587bae53ddb93ec633a1c94e3bd7
➜  sweetpea-py git:(master) ✗ docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS                    NAMES
30c3576d311d        sweetpea/server     "server"            3 seconds ago       Up 2 seconds        0.0.0.0:8080->8080/tcp   stoic_beaver
➜  sweetpea-py git:(master) ✗ export SWEETPEA_EXTERNAL_DOCKER_MGMT=true
➜  sweetpea-py git:(master) ✗ make acceptance
...
➜  sweetpea-py git:(master) ✗ docker stop 30c3576d311d23899fee96a7a2c12ef74502587bae53ddb93ec633a1c94e3bd7
30c3576d311d23899fee96a7a2c12ef74502587bae53ddb93ec633a1c94e3bd7
➜  sweetpea-py git:(master) ✗ docker rm 30c3576d311d23899fee96a7a2c12ef74502587bae53ddb93ec633a1c94e3bd7
30c3576d311d23899fee96a7a2c12ef74502587bae53ddb93ec633a1c94e3bd7
```