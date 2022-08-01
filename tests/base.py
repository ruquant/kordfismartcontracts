import subprocess
from os.path import dirname, join
from unittest import TestCase
import copy

from pytezos import pytezos
from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos.crypto.key import Key
from pytezos.michelson.parse import michelson_to_micheline
from .constants import ALICE_KEY, ALICE_ADDRESS, BOB_ADDRESS, BOB_KEY, CLARE_KEY

LQT_PROVIDER = ALICE_ADDRESS
MANAGER = ALICE_ADDRESS
INITIAL_POOL = 1000000
TZBTC_STORAGE = {
    'tokens': { LQT_PROVIDER: INITIAL_POOL, BOB_ADDRESS: 10**8},
    'allowances': {},
    'admin': MANAGER,
    'total_supply': INITIAL_POOL,
    'token_metadata': {},
}
LQT_STORAGE = {
    'tokens': { LQT_PROVIDER: INITIAL_POOL},
    'allowances': {},
    'admin': MANAGER,
    'total_supply': INITIAL_POOL,
    'token_metadata': {},
}
INITIAL_TOKEN_POOL_IN_DEX = 1000
DEX_STORAGE = {
    'tokenPool': INITIAL_TOKEN_POOL_IN_DEX,
    'xtzPool': 10 ** 9,
    'lqtTotal': INITIAL_POOL,
    'tokenAddress': None,
    'lqtAddress': None,
}
ORACLE_SOURCE_FILE = join(dirname(__file__), './DummyOracle.py')
ORACLE_OUT_DIR = join(dirname(__file__), '../.out_oracle')
ORACLE_COMPILE_COMMAND = '''\
    ~/smartpy-cli/SmartPy.sh compile {source_file} {out_dir} --protocol ithaca
'''


alice_client = pytezos.using(
    shell=ShellQuery(RpcNode('http://localhost:20000')),
    key=Key.from_encoded_key(ALICE_KEY),
)
bob_client = pytezos.using(
    shell=ShellQuery(RpcNode('http://localhost:20000')),
    key=Key.from_encoded_key(BOB_KEY),
)
clare_client = pytezos.using(
    shell=ShellQuery(RpcNode('http://localhost:20000')),
    key=Key.from_encoded_key(CLARE_KEY),
)


class DemoLBBaseTestCase(TestCase):
    """
    Деплоит контракты из demo_lb
    """
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

        context = ExecutionContext(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key=Key.from_encoded_key(ALICE_KEY),
        )
        cls.alice_client = alice_client
        cls.bob_client = bob_client
        cls.clare_client = clare_client
        cls.context = context
        
        # compile oracle mock contract
        p = subprocess.run(ORACLE_COMPILE_COMMAND.format(
            source_file=ORACLE_SOURCE_FILE,
            out_dir=ORACLE_OUT_DIR,
        ), shell=True)
        assert p.returncode == 0, 'Oracle compilation should be successfull.'

        # originate tzBTC and LB contracts
        cls.tzbtc_token = ContractInterface.from_file(
            join(dirname(__file__), '../demo_lb/lqt_fa12.mligo.tz'),
            context,
        )
        cls.lqt_token = ContractInterface.from_file(
            join(dirname(__file__), '../demo_lb/lqt_fa12.mligo.tz'),
            context,
        )
        cls.oracle = ContractInterface.from_file(
            join(ORACLE_OUT_DIR, 'contract/step_000_cont_0_contract.tz'),
            context,
        )
        result = cls.alice_client.bulk(
            cls.tzbtc_token.originate(initial_storage=TZBTC_STORAGE),
            cls.lqt_token.originate(initial_storage=LQT_STORAGE),
            cls.oracle.originate(initial_storage={"XTZ": 1_530_000, "BTC": 45_500_000_000})
        ).send(gas_reserve=10000, min_confirmations=1)  

        # originated tzBTC token
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        cls.tzbtc_token.context.address = originated_address
        # originated LB token
        originated_address = result.opg_result['contents'][1]['metadata']['operation_result']['originated_contracts'][0]
        cls.lqt_token.context.address = originated_address
        # originated oracle
        originated_address = result.opg_result['contents'][2]['metadata']['operation_result']['originated_contracts'][0]
        cls.oracle.context.address = originated_address

        # originate DEX contract
        cls.dex_path = join(dirname(__file__), '../demo_lb/dexter.liquidity_baking.mligo.tz')
        cls.dex_contract = ContractInterface.from_file(cls.dex_path, context)
        dex_storage = copy.deepcopy(DEX_STORAGE)
        dex_storage['lqtAddress'] = cls.lqt_token.context.address
        dex_storage['tokenAddress'] = cls.tzbtc_token.context.address
        cls.initial_dex_storage = dex_storage
        result = cls.dex_contract.originate(
          initial_storage=dex_storage,
          balance=10 ** 9,
        ).send(gas_reserve=10000, min_confirmations=1)
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        cls.dex_contract.context.address = originated_address

        # set LQT admin to DEX contract and transfer tzBTC amount to DEX
        transfer_params = {
            'from': LQT_PROVIDER,
            'to': cls.dex_contract.context.address,
            'value': INITIAL_TOKEN_POOL_IN_DEX,
        }
        cls.alice_client.bulk(
            cls.lqt_token.setAdmin(cls.dex_contract.context.address),
            cls.tzbtc_token.transfer(**transfer_params),
        ).send(gas_reserve=10000, min_confirmations=1)
