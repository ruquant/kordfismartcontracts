from decimal import Decimal


from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY
from ...constants import TEST_GAS_DELTA


class RedeemLBNoUpfrontCommissionTest(MainContractBaseTestCase):

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
            'deposit_index': 10**12,
            'net_credit_index': 10**15,
            'gross_credit_index': 10**18,

            'totalSupply': 200_000_000_000_000,
            'total_net_credit': 23_629_132_000,
            'total_gross_credit': 23_629_132,

            'lb_shares': 27_584,
            'upfront_commission': 10000,

            'liquidity_book': {
                BOB_ADDRESS: {
                    'lb_shares': 13_371,
                    'gross_credit': 13_940_342,
                    'net_credit': 13_940_342_000,
                }
            }
        }
        initial_amount = 175_000_000
        super().setUpClass(initial_storage, initial_amount, btc_version=False)

        transfer_params = {
            'from': ALICE_ADDRESS,
            'to': cls.main_contract.context.address,
            'value': 27_584,
        }
        cls.lqt_token.context.key = Key.from_encoded_key(ALICE_KEY)
        result = cls.lqt_token.transfer(**transfer_params).send(gas_reserve=10000, min_confirmations=1)

    def test_redeem_lb(self):
        main_address = self.main_contract.context.address

        # DEX contract storage
        # tokenPool = 1_000
        # xtzPool = 1_000_000_000
        # lqtTotal = 1_000_000
        bob_balance = self.bob_client.balance()
        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        # Bob redeems LB
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(13_371, 13).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 14_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 14_213)

        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        self.assertEqual(self.main_contract.context.get_balance(), 188_940_342)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 9_688_790)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 9_688_790_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 200_000_000_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.tzbtc_token.storage['tokens'][BOB_ADDRESS](), 100_000_000)
        self.assertAlmostEquals(self.bob_client.balance() - bob_balance, Decimal('12.231361'), delta=TEST_GAS_DELTA)


class PartialRedeemLBTest(MainContractBaseTestCase):

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
            'deposit_index': 10**12,
            'net_credit_index': 10**15,
            'gross_credit_index': 10**18,

            'totalSupply': 200_000_000_000_000,
            'total_net_credit': 23_629_132_000,
            'total_gross_credit': 23_629_132,

            'lb_shares': 27_584,
            'upfront_commission': 10000,

            'liquidity_book': {
                BOB_ADDRESS: {
                    'lb_shares': 13_371,
                    'gross_credit': 13_940_342,
                    'net_credit': 13_940_342_000,
                }
            }
        }
        initial_amount = 175_000_000
        super().setUpClass(initial_storage, initial_amount, btc_version=False)

        transfer_params = {
            'from': ALICE_ADDRESS,
            'to': cls.main_contract.context.address,
            'value': 27_584,
        }
        cls.lqt_token.context.key = Key.from_encoded_key(ALICE_KEY)
        result = cls.lqt_token.transfer(**transfer_params).send(gas_reserve=10000, min_confirmations=1)

    def test_partial_redeem_lb(self):
        main_address = self.main_contract.context.address

        # DEX contract storage
        # tokenPool = 1_000
        # xtzPool = 1_000_000_000
        # lqtTotal = 1_000_000
        bob_balance = self.bob_client.balance()
        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        # Bob partially redeems LB 1
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(7_371, 0).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 20_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 20_213)

        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        self.assertEqual(self.main_contract.context.get_balance(), 182_684_860)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 6_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 6_255_483)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 6_255_482_163)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 15_944_273)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 15_944_272_163)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 200_000_000_000_000)

        self.assertEqual(self.tzbtc_token.storage['tokens'][BOB_ADDRESS](), 100_000_000)
        self.assertAlmostEqual(self.bob_client.balance() - bob_balance, Decimal('6.620_701'), delta=TEST_GAS_DELTA)

        bob_balance = self.bob_client.balance()
        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        # Bob partially redeems LB 2
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(4_000, 0).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 16_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 16_213)

        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        self.assertEqual(self.main_contract.context.get_balance(), 186_855_182)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 2_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 2_085_161)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 2_085_160_721)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 11_773_951)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 11_773_950_721)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 200_000_000_000_000)

        self.assertEqual(self.tzbtc_token.storage['tokens'][BOB_ADDRESS](), 100_000_000)
        self.assertAlmostEqual(self.bob_client.balance() - bob_balance, Decimal('3.720_731'), delta=TEST_GAS_DELTA)

        bob_balance = self.bob_client.balance()
        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        # Bob partially redeems LB 3
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(2_000, 0).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 14_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 14_213)

        with self.assertRaises(KeyError):
            self.tzbtc_token.storage['tokens'][main_address]()

        self.assertEqual(self.main_contract.context.get_balance(), 188_940_343)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 9_688_790)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 9_688_790_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 200_000_000_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.tzbtc_token.storage['tokens'][BOB_ADDRESS](), 100_000_000)
        self.assertAlmostEqual(self.bob_client.balance() - bob_balance, Decimal('1.840_647'), delta=TEST_GAS_DELTA)
