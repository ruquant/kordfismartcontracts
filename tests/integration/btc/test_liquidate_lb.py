from decimal import Decimal


from pytezos.crypto.key import Key


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY, TEST_GAS_DELTA



class LiquidateLBTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'lb_shares': 130_000,
            'tzBTC_shares': 1_480,
            'lb_price': 1_000_000_000,

            'deposit_index': 1_500_000_000_000,
            'net_credit_index': 1_600_000_000_000,
            'gross_credit_index': 1_900_000_000_000,

            'total_gross_credit': 1_200_000_000_000_000,
            'total_net_credit': 1_400_000_000_000_000,
            'totalSupply': 4_000_000_000_000_000,

            'ledger': {
                BOB_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
                CLARE_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
            },
            'liquidity_book': {
                BOB_ADDRESS: {
                    'net_credit': 1_100_000_000_000_000,
                    'gross_credit': 1_000_000_000_000_000,  # $1900
                    'lb_shares': 100_000,  # $200
                },
                CLARE_ADDRESS: {
                    'net_credit': 300_000_000_000_000,
                    'gross_credit': 200_000_000_000_000,
                    'lb_shares': 30_000,
                },
            },

            'upfront_commission': 1_500,  # 1.5%

            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },
        }

        super().setUpClass(initial_storage, btc_version=True)

        cls.alice_client.bulk(
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 1_480,
            }),
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': CLARE_ADDRESS,
                'value': 2_090,
            }),
            cls.lqt_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 130_000,
            }),
            cls.oracle.set_price(1_000_000, 100_000_000_000_000),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_basic_liquidation(self):
        main_address = self.main_contract.context.address
        initial_admin_balance = self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]()

        self.clare_client.bulk(
            self.tzbtc_token.approve(
                value = 2_090,
                spender = self.main_contract.address,
            ),
            self.main_contract.liquidateLB(BOB_ADDRESS, 2_090),
            self.tzbtc_token.approve(
                value = 0,
                spender = self.main_contract.address,
            ),
        ).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 200_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 300_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 30_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 30_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 3_475)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 3_475)

        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][CLARE_ADDRESS]()
        self.assertEqual(self.lqt_token.storage['tokens'][CLARE_ADDRESS](), 100_000)
        self.assertEqual(self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]() - initial_admin_balance, 95)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 30_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 200_000_000_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 300_000_000_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 2_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 2_000_000_000_000_000)


class PartiallyLiquidateLBTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'lb_shares': 130_000,
            'tzBTC_shares': 1_480,
            'lb_price': 1_000_000_000,

            'deposit_index': 1_500_000_000_000,
            'net_credit_index': 1_600_000_000_000,
            'gross_credit_index': 1_900_000_000_000,

            'total_gross_credit': 1_200_000_000_000_000,
            'total_net_credit': 1_400_000_000_000_000,
            'totalSupply': 4_000_000_000_000_000,

            'ledger': {
                BOB_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
                CLARE_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
            },
            'liquidity_book': {
                BOB_ADDRESS: {
                    'net_credit': 1_100_000_000_000_000,
                    'gross_credit': 1_000_000_000_000_000,  # $1900
                    'lb_shares': 100_000,  # $200
                },
                CLARE_ADDRESS: {
                    'net_credit': 300_000_000_000_000,
                    'gross_credit': 200_000_000_000_000,
                    'lb_shares': 30_000,
                },
            },

            'upfront_commission': 1_500,  # 1.5%

            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },
        }

        super().setUpClass(initial_storage, btc_version=True)

        cls.alice_client.bulk(
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 1_480,
            }),
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': CLARE_ADDRESS,
                'value': 2_190,
            }),
            cls.lqt_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 130_000,
            }),
            cls.oracle.set_price(1_000_000, 100_000_000_000_000),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_partial_liquidation(self):
        main_address = self.main_contract.context.address
        initial_admin_balance = self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]()

        # partial liquidation
        self.clare_client.bulk(
            self.tzbtc_token.approve(
                value = 1_000,
                spender = self.main_contract.address,
            ),
            self.main_contract.liquidateLB(BOB_ADDRESS, 1_000),
            self.tzbtc_token.approve(
                value = 0,
                spender = self.main_contract.address,
            ),
        ).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 721_578_947_368_422)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 873_736_842_105_265)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 82_158)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 82_158)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 2_435)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 2_435)

        self.assertEqual(self.tzbtc_token.storage['tokens'][CLARE_ADDRESS](), 1_190)
        self.assertEqual(self.lqt_token.storage['tokens'][CLARE_ADDRESS](), 47_842)
        self.assertEqual(self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]() - initial_admin_balance, 45)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 52_158)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 521_578_947_368_422)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 573_736_842_105_265)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 30_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 200_000_000_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 300_000_000_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 2_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 2_000_000_000_000_000)

        # remainder liquidation
        self.clare_client.bulk(
            self.tzbtc_token.approve(
                value = 1_092,
                spender = self.main_contract.address,
            ),
            self.main_contract.liquidateLB(BOB_ADDRESS, 1_092),
            self.tzbtc_token.approve(
                value = 0,
                spender = self.main_contract.address,
            ),
        ).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 200_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 300_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 30_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 30_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 3_477)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 3_477)

        self.assertEqual(self.tzbtc_token.storage['tokens'][CLARE_ADDRESS](), 98)
        self.assertEqual(self.lqt_token.storage['tokens'][CLARE_ADDRESS](), 100_000)
        self.assertEqual(self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]() - initial_admin_balance, 95)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 30_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 200_000_000_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 300_000_000_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 2_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 2_000_000_000_000_000)
