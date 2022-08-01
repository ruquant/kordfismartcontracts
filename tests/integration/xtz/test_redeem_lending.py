from decimal import Decimal
from datetime import timedelta, datetime
from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError

from ..base import MainContractBaseTestCase
from ...constants import ALICE_KEY, ALICE_ADDRESS, BOB_KEY, BOB_ADDRESS, CLARE_ADDRESS, CLARE_KEY


class RedeemLendingTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        initial_storage = {}
        initial_storage['deposit_index'] = 1_500_000_000_000
        initial_storage['net_credit_index'] = 1_700_000_000_000
        initial_storage['gross_credit_index'] = 1_800_000_000_000
        initial_storage['ledger'] = {
            BOB_ADDRESS: {
                    'balance': 1_000_000_000_000_000,
                    'approvals': {},
                },
                CLARE_ADDRESS: {
                    'balance': 1_000_000_000_000,
                    'approvals': {},
                },
        }
        initial_storage['totalSupply'] = 1_001_000_000_000_000
        initial_amount = 600_000_000
        super().setUpClass(initial_storage, initial_amount)

    def test_redeem(self):
        # Bob redeem available funds
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .redeemLending(500_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        # check contract storage
        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 666_666_666_666_666)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 1_000_000_000_000)
        self.assertAlmostEqual(
            datetime.fromtimestamp(self.main_contract.storage['index_update_dttm']()),
            datetime.now(),
            delta=timedelta(seconds=3),
        )
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_500_000_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_700_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 1_800_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 667_666_666_666_666)

        # check contract balance
        self.assertEqual(self.main_contract.context.get_balance(), 100_000_000)

        # Bob redeems unavailable funds
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            (self.main_contract
                .redeemLending(200_000_000)
                .send(gas_reserve=10000, min_confirmations=1))
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Not enough balance')

        # Claire redeems too much
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(CLARE_KEY)
            (self.main_contract
                .redeemLending(2_000_000)
                .send(gas_reserve=10000, min_confirmations=1))
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'too much amount')

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 666_666_666_666_666)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 1_000_000_000_000)

        # check contract balance
        self.assertEqual(self.main_contract.context.get_balance(), 100_000_000)

        # Admin disables contract
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setIsWorkingStatus(False).send(gas_reserve=10000, min_confirmations=1)

        # BOB redeems available funds
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .redeemLending(100_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 599_999_999_999_999)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 1_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 600_999_999_999_999)

        # check contract balance
        self.assertEqual(self.main_contract.context.get_balance(), 0)
