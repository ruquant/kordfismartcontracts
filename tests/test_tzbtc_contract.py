from os.path import dirname, join
from unittest import TestCase

from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos.crypto.key import Key
from .constants import ALICE_KEY, ALICE_ADDRESS, BOB_ADDRESS

LQT_PROVIDER = ALICE_ADDRESS
MANAGER = ALICE_ADDRESS
INITIAL_POOL = 1000000
# Learn how to convert michelson storage (acquired from ligo contract) to python storage
# INITIAL_POOL = '1000000'
# TZBTC_METADATA = '{Elt 0 (Pair 0 {Elt "decimals" 0x30; Elt "name" 0x4641312e3220544f4b454e; Elt "symbol" 0x544f4b;})}'
# TZBTC_STORAGE = f'Pair {{Elt "{LQT_PROVIDER}" {INITIAL_POOL} {{}} "{MANAGER}" {INITIAL_POOL} {TZBTC_METADATA}'
# not working:
# storage = ContractInterface.storage_from_michelson(TZBTC_STORAGE)
# print('set storage', TZBTC_STORAGE)
# cls.tzbtc_contract.storage_from_michelson(TZBTC_STORAGE)
# print(cls.tzbtc_contract.storage.decode(TZBTC_STORAGE))
TZBTC_STORAGE = {
  'tokens': { ALICE_ADDRESS: INITIAL_POOL},
  'allowances': {},
  'admin': ALICE_ADDRESS,
  'total_supply': INITIAL_POOL,
  'token_metadata': {},
}

class TZBTCSetupTest(TestCase):

    @classmethod
    def setUpClass(cls):
        context = ExecutionContext(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key= Key.from_encoded_key(ALICE_KEY),
        )
        cls.tzbtc_contract = ContractInterface.from_file(
            join(dirname(__file__), '../demo_lb/lqt_fa12.mligo.tz'),
            context,
        )

        result = cls.tzbtc_contract.originate(
          initial_storage=TZBTC_STORAGE,
        ).send(gas_reserve=10000, min_confirmations=1)
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        cls.tzbtc_contract.context.address = originated_address

        cls.maxDiff = None

    def test_transfer(self):
        # check initial tokens amount
        alice_tokens = self.tzbtc_contract.storage['tokens'][ALICE_ADDRESS]()
        self.assertEqual(alice_tokens, INITIAL_POOL)

        # transfer from alice to bob
        transfer_params = {
            'from': ALICE_ADDRESS,
            'to': BOB_ADDRESS,
            'value': 3,
        }
        self.tzbtc_contract.transfer(**transfer_params).send(gas_reserve=10000, min_confirmations=1)

        # check eventual amounts
        bob_tokens = self.tzbtc_contract.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_tokens, 3)
        alice_tokens = self.tzbtc_contract.storage['tokens'][ALICE_ADDRESS]()
        self.assertEqual(alice_tokens, 999997)
