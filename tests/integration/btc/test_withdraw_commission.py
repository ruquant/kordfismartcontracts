from math import ceil
import time


from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class BasicTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial_now = int(time.time()) - 60 * 60 * 24 * 7  # week ago
        initial_storage = {
            'index_update_dttm': cls.initial_now,

            'deposit_index': 1_500_000_000_000,
            'net_credit_index': 1_600_000_000_000,
            'gross_credit_index': 1_900_000_000_000,

            'totalSupply': 4_000_000_000_000_000,
            'total_net_credit': 1_360_000_000_000_000,
            'total_gross_credit': 1_220_000_000_000_000,

            'tzBTC_shares': 3_924,
        }
        super().setUpClass(initial_storage, btc_version=True)

        cls.tzbtc_token.context.key = Key.from_encoded_key(ALICE_KEY)
        cls.tzbtc_token.transfer(**{
            'from': ALICE_ADDRESS,
            'to': cls.main_contract.context.address,
            'value': 3_924,
        }).send(gas_reserve=10000, min_confirmations=1)

    def test_basic(self):
        main_address = self.main_contract.context.address
        initial_tokens = self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]()

        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(CLARE_KEY)
            self.main_contract.withdrawCommission().send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.withdrawCommission().send(gas_reserve=10000, min_confirmations=1)

        dttm_delta = self.main_contract.storage['index_update_dttm']() - self.initial_now
        expected_gross_credit_index = ceil(1_900_000_000_000 * (1_000_000_000_000 + 1459 * dttm_delta) / 1_000_000_000_000)
        expected_net_credit_index = ceil(1_600_000_000_000 * (1_000_000_000_000 + 1313 * dttm_delta) / 1_000_000_000_000)
        expected_deposit_index = 1_500_000_000_000 * (1_000_000_000_000 + 476 * dttm_delta) // 1_000_000_000_000

        self.assertEqual(self.main_contract.storage['gross_credit_index'](), expected_gross_credit_index)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), expected_net_credit_index)
        self.assertEqual(self.main_contract.storage['deposit_index'](), expected_deposit_index)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 3_682)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 3_682)

        self.assertEqual(
            self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]() - initial_tokens,
            242
        )

        self.assertEqual(self.main_contract.context.get_balance(), 0)
