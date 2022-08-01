# Levered Farm Smart Contracts

Smart contracts for levered farms.

## Getting started

Open in Gitpod or

### Install dependencies locally

1. [Docker](https://docs.docker.com/engine/install/)
1. [Poetry](https://python-poetry.org/docs/#installation)
1. [Pytezos dependencies](https://pytezos.org/quick_start.html#requirements) of your OS.
1. Python packages `poetry install`

### Run tests

Tests from `tests` folder, start blockchain sandbox:

    ./scripts/jakartabox.sh

Then:

    pytest tests -v

## Gitpod

Gitpod environment provides:

 - the Tezos client,
 - SmartPy CLI,
 - the Ligo compiler,
 - the Ligo, Archetype and Michelson IDE plugins and syntax extensions,
 - a Michelson debugger.

Could be installed by dockerfile:
 - the Archetype compiler and the [completium-cli](https://completium.com/docs/cli) CLI

## Deploy contract to testnet

We will originate 5 contracts: three are custom LB, one is dummy oracle and one is xtz/tzbtc levered farm.

### Prepare tezos client.

Setup tezos-client to work with testnet ([list](https://tezostaquito.io/docs/rpc_nodes/) of alternative nodes):

    tezos-client --endpoint https://rpc.jakartanet.teztnets.xyz config update

Import key from Temple wallet (or use [faucet](https://teztnets.xyz/)).
Go to Settings -> Reveal private key.
Substitute key and run `tezos-client import secret key alice unencrypted:<key>`
Example:

    tezos-client import secret key alice unencrypted:<key> --force

List known keys and check balance

    tezos-client list known contracts
    tezos-client get balance for alice

You should have more than 10000 xtz on balance.

### Deploy contracts.

Replace `<key>` with private key used above. 
Run command:

    scripts/deploy_to_testnet.sh > log.txt

### Deployed examples

  - "tzBTC" token [tzkt.io](https://jakartanet.tzkt.io/KT1XL6Z8HtgYesw6YtVJYGUaG8ovr2pjh2X7/operations/), [BCD interact](https://better-call.dev/jakartanet/KT1XL6Z8HtgYesw6YtVJYGUaG8ovr2pjh2X7/interact)
  - LB token [tzkt.io](https://jakartanet.tzkt.io/KT1Q3NNe5uQpqEmGLZzMEBToWCXq1hwd532N/operations/), [BCD interact](https://better-call.dev/jakartanet/KT1Q3NNe5uQpqEmGLZzMEBToWCXq1hwd532N/interact)
  - LB CPMM [tzkt.io](https://jakartanet.tzkt.io/KT1Wf2QGQesjo3j95BWHrQNPSgCEdhXvbefj/operations/), [BCD interact](https://better-call.dev/jakartanet/KT1Wf2QGQesjo3j95BWHrQNPSgCEdhXvbefj/interact)
  - Dummy Oracle [tzkt.io](https://jakartanet.tzkt.io/KT1HhsD3RtjA43rspqCecoUd3gK79mGpefZV/operations/), [BCD interact](https://better-call.dev/jakartanet/KT1HhsD3RtjA43rspqCecoUd3gK79mGpefZV/interact)
  - XTZ Levered Farm contract [tzkt.io](https://jakartanet.tzkt.io/KT1XShYE3e9SKjqX8bHeBuCJmw1VQ9vU9RBa/operations/), [BCD interact](https://better-call.dev/jakartanet/KT1XShYE3e9SKjqX8bHeBuCJmw1VQ9vU9RBa/interact)
  - BTC Levered Farm contract [tzkt.io](https://jakartanet.tzkt.io/KT1RtmbkpAbMounPu6HFUww3rgjUCvPrAuKn/operations/), [BCD interact](https://better-call.dev/jakartanet/KT1RtmbkpAbMounPu6HFUww3rgjUCvPrAuKn/interact)

## Deploy to mainnet

1. Set secret key for transactions in `scripts/deploy_to_mainnet.sh`. Change initial storage parameters, e.g. administrator.
2. Run script:

    scripts/deploy_to_mainnet.sh

3. Contract should be displayed or look for originator address at https://tzkt.io.

### Deployed contracts

  - XTZ Levered Farm contract [tzkt.io](https://tzkt.io/KT1RsA2gpKaxk7hwV9arBbYSVAcaoYVV8xXD/operations/), [BCD interact](https://better-call.dev/mainnet/KT1RsA2gpKaxk7hwV9arBbYSVAcaoYVV8xXD/interact)
  - BTC Levered Farm contract [tzkt.io](https://tzkt.io/KT1PztexutMjEytPaFYWPo3KqmDTE95U9S97/operations/), [BCD interact](https://better-call.dev/mainnet/KT1PztexutMjEytPaFYWPo3KqmDTE95U9S97/interact)
