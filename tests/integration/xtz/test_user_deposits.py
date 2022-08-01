from decimal import Decimal
from datetime import timedelta, datetime
from pytezos.crypto.key import Key

from ..base import MainContractBaseTestCase
from ...constants import ALICE_KEY, ALICE_ADDRESS, BOB_KEY, BOB_ADDRESS, TEST_GAS_DELTA

class LendingTest(MainContractBaseTestCase):
    def test_deposit_twice(self):
        initial_bob_balance = self.bob_client.balance()

        # Bob deposits
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .depositLending()
            .with_amount(1000_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        # check Bob balance and deposit
        bob_balance = self.bob_client.balance()
        self.assertAlmostEqual(initial_bob_balance - bob_balance, Decimal('1000'), delta=TEST_GAS_DELTA)

        bob_deposit = self.main_contract.storage['ledger'][BOB_ADDRESS]['balance']()
        self.assertEqual(bob_deposit, 1000_000_000_000_000)
        self.assertAlmostEqual(
            datetime.fromtimestamp(self.main_contract.storage['index_update_dttm']()),
            datetime.now(),
            delta=timedelta(seconds=3),
        )

        # check contract balance
        self.assertEqual(self.main_contract.context.get_balance(), 1_000_000_000)

        # Bob deposits second time
        initial_bob_balance = bob_balance
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .depositLending()
            .with_amount(500_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        # check Bob balance and deposit
        bob_balance = self.bob_client.balance()
        self.assertAlmostEqual(initial_bob_balance - bob_balance, Decimal('500'), delta=TEST_GAS_DELTA)

        bob_deposit = self.main_contract.storage['ledger'][BOB_ADDRESS]['balance']()
        self.assertEqual(bob_deposit, 1500_000_000_000_000)
        self.assertAlmostEqual(
            datetime.fromtimestamp(self.main_contract.storage['index_update_dttm']()),
            datetime.now(),
            delta=timedelta(seconds=3),
        )

        # check contract balance
        self.assertEqual(self.main_contract.context.get_balance(), 1_500_000_000)

    def test_deposit_zero(self):
        initial_bob_balance = self.bob_client.balance()
        initial_contract_balance = self.main_contract.context.get_balance()
        initial_bob_book = self.main_contract.storage['ledger'][BOB_ADDRESS]['balance']()

        # Bob deposits zero
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .depositLending()
            .with_amount(0)
            .send(gas_reserve=10000, min_confirmations=1))

        bob_balance = self.bob_client.balance()
        self.assertAlmostEqual(initial_bob_balance - bob_balance, Decimal('0'), delta=TEST_GAS_DELTA)
        bob_deposit = self.main_contract.storage['ledger'][BOB_ADDRESS]['balance']()
        self.assertEqual(bob_deposit, initial_bob_book)
        self.assertEqual(self.main_contract.context.get_balance(), initial_contract_balance)
        self.assertAlmostEqual(
            datetime.fromtimestamp(self.main_contract.storage['index_update_dttm']()),
            datetime.now(),
            delta=timedelta(seconds=3),
        )

class LendingTestWithIndexes(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        initial_storage = {}
        initial_storage['deposit_index'] = 1_500_000_000_000
        initial_storage['net_credit_index'] = 1_700_000_000_000
        initial_storage['gross_credit_index'] = 1_800_000_000_000
        initial_storage['totalSupply'] = 2_000_000_000_000_000
        initial_storage['ledger'] = {
            BOB_ADDRESS: {
                'balance': 1_000_000_000_000_000,
                'approvals': {},
            },
        }
        super().setUpClass(initial_storage)

    def test_deposit(self):
        # Bob deposits
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .depositLending()
            .with_amount(1_000_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        # check contract storage
        bob_deposit = self.main_contract.storage['ledger'][BOB_ADDRESS]['balance']()
        self.assertEqual(bob_deposit, 1_666_666_666_666_666)
        self.assertAlmostEqual(
            datetime.fromtimestamp(self.main_contract.storage['index_update_dttm']()),
            datetime.now(),
            delta=timedelta(seconds=3),
        )
        self.assertEqual(self.main_contract.storage['totalSupply'](), 2_666_666_666_666_666)
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_500_000_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_700_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 1_800_000_000_000)

        # Admin disables contract
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setIsWorkingStatus(False).send(gas_reserve=10000, min_confirmations=1)

        # Bob deposits again
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .depositLending()
            .with_amount(1_000_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        # check contract storage
        bob_deposit = self.main_contract.storage['ledger'][BOB_ADDRESS]['balance']()
        self.assertEqual(bob_deposit, 2_333_333_333_333_332)
        self.assertAlmostEqual(
            datetime.fromtimestamp(self.main_contract.storage['index_update_dttm']()),
            datetime.now(),
            delta=timedelta(seconds=3),
        )
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_500_000_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_700_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 1_800_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 3_333_333_333_333_332)
