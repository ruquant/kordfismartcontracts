from decimal import Decimal


from pytezos.crypto.key import Key


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY, TEST_GAS_DELTA


class RedeemLBTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'lb_shares': 130_000,
            'tzBTC_shares': 1_480,

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
                    'net_credit': 66_000_000_000_000,
                    'gross_credit': 60_000_000_000_000,
                    'lb_shares': 100_000,
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
                'value': 2_000,
            }),
            cls.lqt_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 130_000,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_basic_redeem_lb(self):
        main_address = self.main_contract.context.address
        bob_initial_balance = self.bob_client.balance()

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(100_000, 100, 25_000_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertAlmostEqual(
            self.bob_client.balance() - bob_initial_balance,
            Decimal('85.419146'),
            delta = TEST_GAS_DELTA
        )

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 30_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 30_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 1_594)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 1_594)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_140_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_334_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 30_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 200_000_000_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 300_000_000_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 2_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 2_000_000_000_000_000)


class PartialRedeemLBTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'lb_shares': 130_000,
            'tzBTC_shares': 1_480,

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
                    'net_credit': 66_000_000_000_000,
                    'gross_credit': 60_000_000_000_000,
                    'lb_shares': 100_000,
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
                'value': 2_000,
            }),
            cls.lqt_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 130_000,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_partial_redeem_lb(self):
        main_address = self.main_contract.context.address

        # Bob partially redeems 60_000 LB
        bob_initial_balance = self.bob_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(60_000, 60, 10_000_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertAlmostEqual(
            self.bob_client.balance() - bob_initial_balance,
            Decimal('50'),
            delta = TEST_GAS_DELTA
        )

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 70_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 70_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 1_549)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 1_549)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_164_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_360_400_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 40_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 24_000_000_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 26_400_000_000_000)

        # Bob partially redeems 30_000 LB
        bob_initial_balance = self.bob_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(30_000, 29, 7_000_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertAlmostEqual(
            self.bob_client.balance() - bob_initial_balance,
            Decimal('23.318_829'),
            delta = TEST_GAS_DELTA
        )

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 40_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 40_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 1_584)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 1_584)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_146_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_340_600_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 10_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 6_000_000_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 6_600_000_000_000)

        # Bob partially redeems 10_000 LB
        bob_initial_balance = self.bob_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(10_000, 9, 4_000_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertAlmostEqual(
            self.bob_client.balance() - bob_initial_balance,
            Decimal('6.183_122'),
            delta = TEST_GAS_DELTA
        )

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 30_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 30_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 1_596)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 1_596)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_140_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_334_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)
