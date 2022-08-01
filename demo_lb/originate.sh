#!/usr/bin/env bash

set -e

export TEZOS_CLIENT_UNSAFE_DISABLE_DISCLAIMER=yes
# tezos-client --endpoint https://rpc.jakartanet.teztnets.xyz config update

LQT_PROVIDER=$(tezos-client list known contracts | grep '^alice:' | cut -d' ' -f2)
MANAGER=$(tezos-client list known contracts | grep '^alice:' | cut -d' ' -f2)
INITIAL_POOL=1000000
TOKEN_METADATA='{Elt 0 (Pair 0 {Elt "decimals" 0x30; Elt "name" 0x4641312e3220544f4b454e; Elt "symbol" 0x544f4b;})}'
LQT_METADATA='{Elt 0 (Pair 0 {Elt "decimals" 0x30; Elt "name" 0x5065746572205069706572207069636b65642061207065636b206f66207069636b6c656420706570706572732e; Elt "symbol" 0x4c5154;})}'

echo LQT_PROVIDER=$LQT_PROVIDER
echo MANAGER=$MANAGER
echo INITIAL_POOL=$INITIAL_POOL
echo TOKEN_METADATA=$TOKEN_METADATA

# Originate token for exchange with Dex contract; LQT interface does not matter
tezos-client originate contract token transferring 0 from alice running demo_lb/lqt_fa12.mligo.tz \
              --init "Pair {Elt \"${LQT_PROVIDER}\" ${INITIAL_POOL}} {} \"${MANAGER}\" ${INITIAL_POOL} ${TOKEN_METADATA}" \
              --burn-cap 10 \
              --force
TOKEN=$(tezos-client list known contracts | grep '^token:' | cut -d' ' -f2)
echo TOKEN=$TOKEN

# Originate Liquidity token
tezos-client originate contract lqt transferring 0 from alice running demo_lb/lqt_fa12.mligo.tz \
              --init "Pair {Elt \"${LQT_PROVIDER}\" ${INITIAL_POOL}} {} \"${MANAGER}\" ${INITIAL_POOL} ${LQT_METADATA}" \
              --burn-cap 10 \
              --force
LQT=$(tezos-client list known contracts | grep '^lqt:' | cut -d' ' -f2)
echo LQT=$LQT

# Originate Dex contract
tezos-client originate contract dexter transferring 0 from alice running demo_lb/dexter.liquidity_baking.mligo.tz \
              --init "Pair 1000 1000000000 ${INITIAL_POOL} \"${TOKEN}\" \"${LQT}\"" \
              --burn-cap 10 \
              --force
DEXTER=$(tezos-client list known contracts | grep '^dexter:' | cut -d' ' -f2)
echo DEXTER=$DEXTER

# Compile parameter:
#   ligo compile parameter demo_lb/lqt_fa12.mligo "SetAdmin({ admin = (\"KT1FCqeSjM5ncGrumeuZcQ6vn5kWJM1w5ya5\": address ) })" --entry-point main
tezos-client transfer 0 from alice to ${LQT} --arg "(Right (Left (Right \"${DEXTER}\")))"

# Transfer xtz to DEXTER
tezos-client transfer 1000 from alice to $DEXTER
# tezos-client transfer 1000 from alice to KT1D6i56EE4DX7uMnpnM6w7AT15YxbDsnYr2

# Transfer Token amount to DEXTER
tezos-client from fa1.2 contract $TOKEN transfer 1000 from alice to $DEXTER --burn-cap 2
# example:
# tezos-client from fa1.2 contract KT1S4mGFwH2jF2BqXc9CszeHv9XdYTa9yQq5 transfer 1000 from alice to KT1D6i56EE4DX7uMnpnM6w7AT15YxbDsnYr2 --burn-cap 2
