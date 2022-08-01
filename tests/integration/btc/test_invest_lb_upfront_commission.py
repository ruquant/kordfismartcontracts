from decimal import Decimal


from pytezos.crypto.key import Key


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY
from ...constants import TEST_GAS_DELTA


class InvestWithUpfrontTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_upfront_commission(self):
        main_address = self.main_contract.context.address

        # Bob deposits 0.1 BTC
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 10**7,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending(10**7).send(gas_reserve=10000, min_confirmations=1)

        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 0,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)
        
        # Admin setups 0.5 upfront commission
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setUpfrontCommission(500).send(gas_reserve=10000, min_confirmations=1)
        admin_balance = self.alice_client.balance()

        self.assertEqual(self.main_contract.storage['upfront_commission'](), 500)

        # Bob invests LB
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 50_000_000, 
            mintzBTCTokensBought = 40, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 150_000_000, 
            minLqtMinted = 140_000,
        ).with_amount(200_500_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0.5'),  # upfront commission
        )

        # Admin setups 1.5 upfront commission
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setUpfrontCommission(1_500).send(gas_reserve=10000, min_confirmations=1)
        admin_balance = self.alice_client.balance()

        self.assertEqual(self.main_contract.storage['upfront_commission'](), 1_500)

        # Bob invests LB
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 40, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 150_000_000, 
            minLqtMinted = 140_000,
        ).with_amount(152_250_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('2.25'),  # upfront commission
        )
