from os.path import dirname, join
from unittest import TestCase

from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos.crypto.key import Key
from .constants import ALICE_KEY, ALICE_ADDRESS, BOB_ADDRESS

INITIAL_POOL = 1000
INITIAL_STORAGE = {
  'tokens': { ALICE_ADDRESS: INITIAL_POOL},
  'allowances': {},
  'admin': ALICE_ADDRESS,
  'total_supply': INITIAL_POOL,
  'token_metadata': {},
}
class LQTUnitTest(TestCase):
    def test_approve(self):
        context = ExecutionContext(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key= Key.from_encoded_key(ALICE_KEY),
        )
        lqt_token = ContractInterface.from_file(
            join(dirname(__file__), '../demo_lb/lqt_fa12.mligo.tz'),
            context,
        )
        result = lqt_token.approve(spender=BOB_ADDRESS, value=10).run_code(
            storage=INITIAL_STORAGE)
        self.assertEqual(0, len(result.operations))
        self.assertEqual(
            result.storage['allowances'],
            {
                ('KT1BEqzn5Wx8uJrZNvuS9DVHmLvG9td3fDLi', BOB_ADDRESS): 10,
            },
        )
