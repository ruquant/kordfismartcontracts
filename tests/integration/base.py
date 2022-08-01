import subprocess
from os.path import dirname, join

from deepmerge import always_merger
from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos.crypto.key import Key
from pytezos.michelson.parse import michelson_to_micheline
from ..constants import ALICE_KEY, ALICE_ADDRESS
from ..base import DemoLBBaseTestCase


XTZ_SOURCE_FILE = join(dirname(__file__), '../../src/LeveragedFarmLendingSmartContract.py')
BTC_SOURCE_FILE = join(dirname(__file__), '../../src/BTCLeveragedFarmLendingSmartContract.py')
OUT_DIR = join(dirname(__file__), '../../.out')
CONTRACT_COMPILE_COMMAND = '''\
    ADMIN_ADDRESS={administrator} \
    LIQUIDITY_BAKING_ADDRESS={dex_address} \
    FA_TZBTC_ADDRESS={tzbtc_address} \
    FA_LB_TOKEN_ADDRESS={lb_token_address} \
    ORACLE_ADDRESS={oracle_address} \
    ~/smartpy-cli/SmartPy.sh compile {source_file} {out_dir} --protocol ithaca
'''

class MainContractBaseTestCase(DemoLBBaseTestCase):
    @classmethod
    def setUpClass(cls, initial_storage_update = None, initial_amount = None, btc_version = False):
        super().setUpClass()

        # compile SmartPy contracts with proper LB contracts
        p = subprocess.run(CONTRACT_COMPILE_COMMAND.format(
            administrator=ALICE_ADDRESS,
            dex_address=cls.dex_contract.context.address,
            tzbtc_address=cls.tzbtc_token.context.address,
            lb_token_address=cls.lqt_token.context.address,
            oracle_address=cls.oracle.context.address,
            source_file=(BTC_SOURCE_FILE if btc_version else XTZ_SOURCE_FILE),
            out_dir=OUT_DIR,
        ), shell=True)
        assert p.returncode == 0, 'Contract compilation should be successfull.'

        # get initial storage
        context = ExecutionContext(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key=Key.from_encoded_key(ALICE_KEY),
        )
        helper_contract = ContractInterface.from_file(
            join(dirname(__file__), '../../.out/contract/step_000_cont_0_contract.tz'),
            context,
        )
        storage_value = michelson_to_micheline(open(
            join(dirname(__file__), '../../.out/contract/step_000_cont_0_storage.tz'),
        ).read())
        helper_contract.storage_from_micheline(storage_value)
        initial_storage = helper_contract.storage()
        if initial_storage_update:
            initial_storage = always_merger.merge(initial_storage, initial_storage_update)

        # originate contract
        cls.main_contract = ContractInterface.from_file(
            join(dirname(__file__), '../../.out/contract/step_000_cont_0_contract.tz'),
            context,
        )
        result = cls.main_contract.originate(
            initial_storage=initial_storage,
            balance=initial_amount or 0,
        ).send(gas_reserve=10000, min_confirmations=1)
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        cls.main_contract.context.address = originated_address
