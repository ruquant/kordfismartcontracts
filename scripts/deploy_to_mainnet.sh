#!/usr/bin/env bash

set -e

SECRET_KEY="changeme"
RPC_NODE="https://mainnet.smartpy.io/"
tezos-client --endpoint	$RPC_NODE config update
tezos-client import secret key alice unencrypted:$SECRET_KEY --force

ADMIN="tz1ZYsWRZeWj3KujrqnomRg1kmrduGUq1jqt"
DEX="KT1TxqZ8QtKvLu3V3JH7Gx58n7Co8pgtpQU5"
TZBTC_TOKEN="KT1PWx2mnDueood7fEmfbBDKx1D9BAnnXitn"
LQT="KT1AafHA1C1vk959wvHWBispY9Y2f3fxBUUo"
ORACLE="KT1P8Ep9y8EsDSD9YkvakWnDvF2orDcpYXSq"

# Deploy xtz contract
ADMIN_ADDRESS=${ADMIN} \
LIQUIDITY_BAKING_ADDRESS=${DEX} \
FA_TZBTC_ADDRESS=${TZBTC_TOKEN} \
FA_LB_TOKEN_ADDRESS=${LQT} \
ORACLE_ADDRESS=${ORACLE} \
    ~/smartpy-cli/SmartPy.sh compile src/LeveragedFarmLendingSmartContract.py .out --protocol ithaca

~/smartpy-cli/SmartPy.sh originate-contract \
    --code .out/contract/step_000_cont_0_contract.json \
    --storage .out/contract/step_000_cont_0_storage.json \
    --rpc $RPC_NODE \
    --private-key $SECRET_KEY

# Deploy btc contract
ADMIN_ADDRESS=${ADMIN} \
LIQUIDITY_BAKING_ADDRESS=${DEX} \
FA_TZBTC_ADDRESS=${TZBTC_TOKEN} \
FA_LB_TOKEN_ADDRESS=${LQT} \
ORACLE_ADDRESS=${ORACLE} \
    ~/smartpy-cli/SmartPy.sh compile src/BTCLeveragedFarmLendingSmartContract.py .out --protocol ithaca

~/smartpy-cli/SmartPy.sh originate-contract \
    --code .out/contract/step_000_cont_0_contract.json \
    --storage .out/contract/step_000_cont_0_storage.json \
    --rpc $RPC_NODE \
    --private-key $SECRET_KEY
