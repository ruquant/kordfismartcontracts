from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class InvestLeverageTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        initial_storage = {
            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },
            'deposit_index': 10**15,
            'net_credit_index': 10**18,
            'gross_credit_index': 10**21,

            'is_working': True,
            # no upfront commission
            'upfront_commission': 0,
        }
        super().setUpClass(initial_storage, btc_version=True)

    def test_different_leverages(self):
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

        # Bob invest LB leverage = 1.5

        # DEX storage:
        # tokenPool 10^3
        # xtzPool 10^9
        # lqtTotal 10^6
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 50_000_000, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 150_000_000, 
            minLqtMinted = 0,
        ).with_amount(200_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 142_863)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 142_863)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 9_999_910)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 9_999_910)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 90_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 90_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 142_863)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 90_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 90_000_000)

        self.assertEqual(self.main_contract.context.get_balance(), 0)

        # Bob invest LB leverage = 2

        # DEX storage:
        # tokenPool 1_090
        # xtzPool 1_199_950_000
        # lqtTotal 1_142_863
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 100_000_000, 
            minLqtMinted = 0,
        ).with_amount(100_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 238_105)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 238_105)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 9_999_819)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 9_999_819)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 181_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 181_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 238_105)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 181_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 181_000_000)

        self.assertEqual(self.main_contract.context.get_balance(), 0)

        # Bob invest LB leverage = 3.99

        # DEX storage:
        # tokenPool 1_181
        # xtzPool 1_299_950_000
        # lqtTotal 238_105
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 99,
            minXtzBought = 99_500_000,
            amount2Lqt = 199_500_000, 
            minLqtMinted = 0,
        ).with_amount(100_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 444_025)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 444_025)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 9_999_507)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 9_999_507)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 493_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 493_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 444_025)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 493_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 493_000_000)

        self.assertEqual(self.main_contract.context.get_balance(), 0)

        # Bob invest LB leverage = 4.1

        # DEX storage:
        # tokenPool 1_493
        # xtzPool 1_398_999_766
        # lqtTotal 1_444_025
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.investLB(
                amount2tzBTC = 0, 
                mintzBTCTokensBought = 0, 
                tzBTC2xtz = 6,
                minXtzBought = 5_025_000,
                amount2Lqt = 10_025_000, 
                minLqtMinted = 0,
            ).with_amount(5_000_000).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')


class InvestLeverageWithDisabledStatusTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        initial_storage = {
            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },
            'deposit_index': 10**15,
            'net_credit_index': 10**18,
            'gross_credit_index': 10**21,

            'is_working': False,
            # no upfront commission
            'upfront_commission': 0,
        }
        super().setUpClass(initial_storage, btc_version=True)

    def test_different_leverages_with_disabled_status(self):
        InvestLeverageTest.test_different_leverages(self)
