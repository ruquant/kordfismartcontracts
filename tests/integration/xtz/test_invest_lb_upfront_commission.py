from decimal import Decimal


from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class InvestWithUpfrontTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=False)

    def test_different_leverages(self):
        main_address = self.main_contract.context.address

        # Bob deposits 200 xtz
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending().with_amount(2 * 10**8).send(gas_reserve=10000, min_confirmations=1)
        
        # Admin setups 0.5 upfront commission
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setUpfrontCommission(500).send(gas_reserve=10000, min_confirmations=1)
        admin_balance = self.alice_client.balance()

        self.assertEqual(self.main_contract.storage['upfront_commission'](), 500)

        # Bob invests LB with extra tzBTC 10
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 10,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 15_412_504,
            mintzBTCTokensBought = 15,
            amount2Lqt = 14_587_496,
            minLqtMinted = 14_366,
            tzBTCShares = 10,
        ).with_amount(15_075_000).send(gas_reserve=10000, min_confirmations=1)

        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 0,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 14_366)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 14_366)

        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        # Bob's tokens
        self.assertEqual(self.tzbtc_token.storage['tokens'][BOB_ADDRESS](), 99_999_990)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0.075'),  # upfront commission
        )

        # Admin setups 1.5 upfront commission
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setUpfrontCommission(1_500).send(gas_reserve=10000, min_confirmations=1)
        admin_balance = self.alice_client.balance()

        self.assertEqual(self.main_contract.storage['upfront_commission'](), 1_500)

        # Bob invests LB with extra tzBTC 15
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 15,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 5_000_000,
            mintzBTCTokensBought = 4,
            amount2Lqt = 15_000_000,
            minLqtMinted = 10_000,
            tzBTCShares = 15,
        ).with_amount(15_075_000).send(gas_reserve=10000, min_confirmations=1)

        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 0,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)
    
        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 29_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 29_213)

        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        # Bob's tokens
        self.assertEqual(self.tzbtc_token.storage['tokens'][BOB_ADDRESS](), 99_999_975)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0.075'),  # upfront commission
        )
