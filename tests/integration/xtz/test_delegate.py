from decimal import Decimal
from math import ceil

from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY
from ...constants import TEST_GAS_DELTA


class DelegationsTest(MainContractBaseTestCase):
    
    def test_basic(self):
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setDelegate(BOB_ADDRESS).send(gas_reserve=10000, min_confirmations=1)

        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(CLARE_KEY)
            self.main_contract.setDelegate(CLARE_ADDRESS).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.default().with_amount(5_000_000).send(gas_reserve=10000, min_confirmations=1)

        initial_admin_balance = self.alice_client.balance()

        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.withdrawCommission().send(gas_reserve=10000, min_confirmations=1)

        self.assertAlmostEqual(
            self.alice_client.balance() - initial_admin_balance,
            Decimal('5.000_000'),
            delta=TEST_GAS_DELTA,
        )

        self.bob_client.bulk(
            self.main_contract.depositLending().with_amount(2_111_111),
            self.main_contract.default().with_amount(7_111_222),
        ).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.main_contract.storage['deposit_index'](), 4_368_473_756_235)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 2_111_111_000_000)
