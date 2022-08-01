#!/usr/bin/env bash
set -e

image=oxheadalpha/flextesa:latest
script=jakartabox

# macos users: https://gitlab.com/tezos/flextesa/blob/master/README.md#macosx-users
export PATH="/usr/local/opt/coreutils/libexec/gnubin:/usr/local/opt/util-linux/bin:$PATH"

docker run --rm --name test_sandbox --detach -p 20000:20000 \
       -e block_time=2 \
       "$image" "$script" start

echo "Waiting testbox to start"
until docker exec test_sandbox tezos-client get timestamp >/dev/null 2>&1
do
  sleep 2
done
echo "Testbox started"

docker exec test_sandbox tezos-client import secret key clare unencrypted:edsk2jkrThhmvGxhyhvDvCKLcbKeGMsTdop1Ko6QSzA2Tw2Cxx7rPi >/dev/null
docker exec test_sandbox tezos-client transfer 1000000 from bob to clare --burn-cap 2 >/dev/null
docker exec test_sandbox tezos-client reveal key for clare >/dev/null
echo "Clare address created"
