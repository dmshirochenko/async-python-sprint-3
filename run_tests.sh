#!/bin/sh

set -e

docker-compose up -d --build --renew-anon-volumes
docker logs -f test-service
exitcode="$(docker inspect test-service --format={{.State.ExitCode}})"
docker-compose down --remove-orphans --volumes
exit "$exitcode"