#!/usr/bin/env bash

set -e

export TEZOS_CLIENT_UNSAFE_DISABLE_DISCLAIMER=yes
tezos-client --endpoint https://jakartanet.smartpy.io/ config update
tezos-client import secret key alice unencrypted:<key> --force

# ligo compile contract \
#     demo_lb/lqt_fa12.mligo \
#     -e main \
#     --output-file demo_lb/lqt_fa12.mligo.tz \
#     -p ithaca

# ligo compile contract \
#     demo_lb/dexter.liquidity_baking.mligo \
#     -e main \
#     --output-file demo_lb/dexter.liquidity_baking.mligo.tz \
#     -p ithaca

LQT_PROVIDER=$(tezos-client list known contracts | grep '^alice:' | cut -d' ' -f2)
MANAGER=$(tezos-client list known contracts | grep '^alice:' | cut -d' ' -f2)
INITIAL_POOL=10000000
TOKEN_METADATA='{Elt 0 (Pair 0 {Elt "decimals" 0x30; Elt "name" 0x4641312e3220544f4b454e; Elt "symbol" 0x544f4b;})}'
LQT_METADATA='{Elt 0 (Pair 0 {Elt "decimals" 0x30; Elt "name" 0x5065746572205069706572207069636b65642061207065636b206f66207069636b6c656420706570706572732e; Elt "symbol" 0x4c5154;})}'

echo LQT_PROVIDER=$LQT_PROVIDER
echo MANAGER=$MANAGER
echo INITIAL_POOL=$INITIAL_POOL
echo TOKEN_METADATA=$TOKEN_METADATA

# Originate "tzBTC" token for exchange with Dex contract
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
              --init "Pair 1000000 10000000000 ${INITIAL_POOL} \"${TOKEN}\" \"${LQT}\"" \
              --burn-cap 10 \
              --force
DEXTER=$(tezos-client list known contracts | grep '^dexter:' | cut -d' ' -f2)
echo DEXTER=$DEXTER

# Set admin for LQT contract from alice to DEX contract
tezos-client transfer 0 from alice to ${LQT} --arg "(Right (Left (Right \"${DEXTER}\")))" --burn-cap 10

# Transfer xtz to DEX contract
tezos-client transfer 10000 from alice to $DEXTER --burn-cap 10

# Transfer Token amount to DEXcontract
tezos-client from fa1.2 contract $TOKEN transfer 1000000 from alice to $DEXTER --burn-cap 2

# Compile and deploy dummy oracle
~/smartpy-cli/SmartPy.sh compile tests/DummyOracle.py .out_oracle --protocol ithaca
tezos-client originate contract oracle transferring 0 from alice running .out_oracle/contract/step_000_cont_0_contract.tz \
              --init "{Elt \"BTC\" 21520000000; Elt \"XTZ\" 1530000}" \
              --burn-cap 10 \
              --force
ORACLE=$(tezos-client list known contracts | grep '^oracle:' | cut -d' ' -f2)
echo ORACLE=$ORACLE

# Deploy xtz contract
ADMIN_ADDRESS=${MANAGER} \
LIQUIDITY_BAKING_ADDRESS=${DEXTER} \
FA_TZBTC_ADDRESS=${TOKEN} \
FA_LB_TOKEN_ADDRESS=${LQT} \
ORACLE_ADDRESS=${ORACLE} \
    ~/smartpy-cli/SmartPy.sh compile src/LeveragedFarmLendingSmartContract.py .out --protocol ithaca

~/smartpy-cli/SmartPy.sh originate-contract \
    --code .out/contract/step_000_cont_0_contract.json \
    --storage .out/contract/step_000_cont_0_storage.json \
    --rpc https://jakartanet.smartpy.io \
    --private-key <key>

# Deploy btc contract
ADMIN_ADDRESS=${MANAGER} \
LIQUIDITY_BAKING_ADDRESS=${DEXTER} \
FA_TZBTC_ADDRESS=${TOKEN} \
FA_LB_TOKEN_ADDRESS=${LQT} \
ORACLE_ADDRESS=${ORACLE} \
    ~/smartpy-cli/SmartPy.sh compile src/BTCLeveragedFarmLendingSmartContract.py .out --protocol ithaca

~/smartpy-cli/SmartPy.sh originate-contract \
    --code .out/contract/step_000_cont_0_contract.json \
    --storage .out/contract/step_000_cont_0_storage.json \
    --rpc https://jakartanet.smartpy.io \
    --private-key <key>
