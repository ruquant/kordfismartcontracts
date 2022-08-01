import math
from decimal import Decimal
from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_KEY, BOB_KEY, BOB_ADDRESS, ALICE_ADDRESS


class InvestLBDummyTest(MainContractBaseTestCase):
    def test_dummy_invest(self):
        """
        Invest with any parameters
        """
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        (self.main_contract
            .depositLending()
            .with_amount(1_000_000_000)
            .send(gas_reserve=10000, min_confirmations=1))
        initial_admin_balance = self.alice_client.balance()

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .investLB(20_000_000, 0, 10_000_000, 0, 0)
            .with_amount(15_000_000 + 150_000)  # +150_000 for upfront commission
            .send(gas_reserve=10000, min_confirmations=1))

        # check contract storage
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 5_748_628_000_000)
        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 5_748_628_000_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 9804)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 5_748_628_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 5_748_628_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 9804)

        # main contact has no tzBTC
        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][self.main_contract.context.address]()
 
        self.assertEqual(
            self.tzbtc_token.storage['tokens'][BOB_ADDRESS](),
            100_000_000,
        )

        # main contract balance
        self.assertEqual(
            self.main_contract.context.get_balance(),
            994_251_372,
        )

        # admin balance delta
        self.assertEqual(
            self.alice_client.balance() - initial_admin_balance,
            Decimal('0.150_000'),
        )


class InvestLBFailAbusedLeverageTest(MainContractBaseTestCase):
    def test_fail_abused_leverage(self):
        """
        Abusing return tzBTC to make bad farm entry
        """
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        (self.main_contract
            .depositLending()
            .with_amount(1_000_000_000)
            .send(gas_reserve=10000, min_confirmations=1))
        initial_admin_balance = self.alice_client.balance()

        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            (self.main_contract
                .investLB(28_000_000, 0, 2_000_000, 0, 0)
                .with_amount(15_000_000 + 150_000)  # +150_000 for upfront commission
                .send(gas_reserve=10000, min_confirmations=1))
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'negative balance delta error')
