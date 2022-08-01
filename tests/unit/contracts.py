import subprocess
import pytest
import copy
from pytezos import pytezos
from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos.crypto.key import Key
from os.path import dirname, join
from .constants import ALICE_KEY, ALICE_ADDRESS
from ..base import DEX_STORAGE, TZBTC_STORAGE, LQT_STORAGE, LQT_PROVIDER, INITIAL_TOKEN_POOL_IN_DEX

dex_contract = None
another_dex_contract = None
tzbtc_token = None
lqt_token = None
oracle = None
xtz_compiled = False
btc_compiled = False
contracts_originated = False

XTZ_SOURCE_FILE = join(dirname(__file__), '../../src/LeveragedFarmLendingSmartContract.py')
BTC_SOURCE_FILE = join(dirname(__file__), '../../src/BTCLeveragedFarmLendingSmartContract.py')
XTZ_OUT_DIR = join(dirname(__file__), '../../.out_unit_xtz')
BTC_OUT_DIR = join(dirname(__file__), '../../.out_unit_xtz')
DEFAULT_COMPILE_COMMAND = '~/smartpy-cli/SmartPy.sh compile {source_file} {out_dir} --protocol ithaca'
EXTENDED_CONTRACT_COMPILE_COMMAND = '''\
    ADMIN_ADDRESS={administrator} \
    LIQUIDITY_BAKING_ADDRESS={dex_address} \
    FA_TZBTC_ADDRESS={tzbtc_address} \
    FA_LB_TOKEN_ADDRESS={lb_token_address} \
    ~/smartpy-cli/SmartPy.sh compile {source_file} {out_dir} --protocol ithaca
'''
ORACLE_SOURCE_FILE = join(dirname(__file__), '../DummyOracle.py')
ORACLE_OUT_DIR = join(dirname(__file__), '../../.out_oracle')
ORACLE_COMPILE_COMMAND = '''\
    ~/smartpy-cli/SmartPy.sh compile {source_file} {out_dir} --protocol ithaca
'''

def get_demo_lb_contracts():
    global contracts_originated
    global dex_contract
    global another_dex_contract
    global tzbtc_token
    global lqt_token
    global oracle
    if not contracts_originated:
        alice_client = pytezos.using(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key=Key.from_encoded_key(ALICE_KEY),
        )
        context = ExecutionContext(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key=Key.from_encoded_key(ALICE_KEY),
        )

        # compile oracle mock contract
        p = subprocess.run(ORACLE_COMPILE_COMMAND.format(
            source_file=ORACLE_SOURCE_FILE,
            out_dir=ORACLE_OUT_DIR,
        ), shell=True)
        assert p.returncode == 0, 'Oracle compilation should be successfull.'

        # originate tzBTC and LB contracts
        tzbtc_token = ContractInterface.from_file(
            join(dirname(__file__), '../../demo_lb/lqt_fa12.mligo.tz'),
            context,
        )
        lqt_token = ContractInterface.from_file(
            join(dirname(__file__), '../../demo_lb/lqt_fa12.mligo.tz'),
            context,
        )
        oracle = ContractInterface.from_file(
            join(ORACLE_OUT_DIR, 'contract/step_000_cont_0_contract.tz'),
            context,
        )
        result = alice_client.bulk(
            tzbtc_token.originate(initial_storage=TZBTC_STORAGE),
            lqt_token.originate(initial_storage=LQT_STORAGE),
            oracle.originate(initial_storage={"XTZ": 1_530_000, "BTC": 45_500_000_000})
        ).send(gas_reserve=10000, min_confirmations=1)  

        # originated tzBTC token
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        tzbtc_token.context.address = originated_address
        # originated LB token
        originated_address = result.opg_result['contents'][1]['metadata']['operation_result']['originated_contracts'][0]
        lqt_token.context.address = originated_address
        # originated oracle
        originated_address = result.opg_result['contents'][2]['metadata']['operation_result']['originated_contracts'][0]
        oracle.context.address = originated_address

        # originate DEX contract
        dex_contract = ContractInterface.from_file(
            join(dirname(__file__), '../../demo_lb/dexter.liquidity_baking.mligo.tz'),
            context,
        )
        dex_storage = copy.deepcopy(DEX_STORAGE)
        dex_storage['lqtAddress'] = lqt_token.context.address
        dex_storage['tokenAddress'] = tzbtc_token.context.address
        result = dex_contract.originate(
          initial_storage=dex_storage,
          balance=10 ** 9,
        ).send(gas_reserve=10000, min_confirmations=1)
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        dex_contract.context.address = originated_address

        # originate another dex contract
        another_dex_contract = ContractInterface.from_file(
            join(dirname(__file__), '../../demo_lb/dexter.liquidity_baking.mligo.tz'),
            context,
        )
        result = another_dex_contract.originate(
          initial_storage=dex_storage,
          balance=10 ** 9,
        ).send(gas_reserve=10000, min_confirmations=1)
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        another_dex_contract.context.address = originated_address

        alice_client.bulk(
            # set LQT admin to DEX contract and transfer tzBTC amount to DEX
            lqt_token.setAdmin(dex_contract.context.address),
            tzbtc_token.transfer(**{
                'from': LQT_PROVIDER,
                'to': dex_contract.context.address,
                'value': INITIAL_TOKEN_POOL_IN_DEX,
            }),
            # and for another dex contract
            tzbtc_token.transfer(**{
                'from': LQT_PROVIDER,
                'to': another_dex_contract.context.address,
                'value': INITIAL_TOKEN_POOL_IN_DEX,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

        contracts_originated = True
    return {
        'dex_contract': dex_contract,
        'tzbtc_token' : tzbtc_token,
        'lqt_token': lqt_token,
        'oracle': oracle,
        'another_dex_contract': another_dex_contract,
    }

def get_xtz_compiled_filepath():
    global xtz_compiled
    if not xtz_compiled:
        contracts = get_demo_lb_contracts()
        # compile SmartPy contracts with proper LB contracts
        p = subprocess.run(EXTENDED_CONTRACT_COMPILE_COMMAND.format(
            administrator=ALICE_ADDRESS,
            dex_address=contracts['dex_contract'].context.address,
            tzbtc_address=contracts['tzbtc_token'].context.address,
            lb_token_address=contracts['lqt_token'].context.address,
            source_file=XTZ_SOURCE_FILE,
            out_dir=XTZ_OUT_DIR,
        ), shell=True)
        assert p.returncode == 0, 'Contract compilation should be successfull.'
        xtz_compiled = True
    return join(XTZ_OUT_DIR, 'contract/step_000_cont_0_contract.tz')

def get_btc_compiled_filepath():
    global btc_compiled
    if not btc_compiled:
        contracts = get_demo_lb_contracts()
        # compile SmartPy contracts with proper LB contracts
        p = subprocess.run(EXTENDED_CONTRACT_COMPILE_COMMAND.format(
            administrator=ALICE_ADDRESS,
            dex_address=contracts['dex_contract'].context.address,
            tzbtc_address=contracts['tzbtc_token'].context.address,
            lb_token_address=contracts['lqt_token'].context.address,
            source_file=BTC_SOURCE_FILE,
            out_dir=BTC_OUT_DIR,
        ), shell=True)
        assert p.returncode == 0, 'Contract compilation should be successfull.'
        btc_compiled = True
    return join(BTC_OUT_DIR, 'contract/step_000_cont_0_contract.tz')
