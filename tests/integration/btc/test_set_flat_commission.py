from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS


class SetUpfronCommissionTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        # Forbidden case
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.setUpfrontCommission(0).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # Normal cases
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setUpfrontCommission(2_000).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.main_contract.storage['upfront_commission'](), 2_000)

        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setUpfrontCommission(1_500).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.main_contract.storage['upfront_commission'](), 1_500)

        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setUpfrontCommission(500).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.main_contract.storage['upfront_commission'](), 500)

        # max value error
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
            self.main_contract.setUpfrontCommission(2_001).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'upfront commission max value error')
