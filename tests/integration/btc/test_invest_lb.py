from decimal import Decimal
from math import ceil
from time import time


from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY, TEST_GAS_DELTA


class InvesLBTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls.initial_now = int(time()) - 60 * 60 * 24 * 7  # week ago

        initial_storage = {
            'index_update_dttm': cls.initial_now,

            'lb_shares': 130_000,
            'tzBTC_shares': 1_480,

            'deposit_index': 1_500_000_000_000,
            'net_credit_index': 1_600_000_000_000,
            'gross_credit_index': 1_900_000_000_000,

            'total_gross_credit': 1_200_000_000_000_000,
            'total_net_credit': 1_400_000_000_000_000,
            'totalSupply': 2_000_000_000_000_000,

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
                    'gross_credit': 1_000_000_000_000_000,
                    'lb_shares': 100_000,
                },
                CLARE_ADDRESS: {
                    'net_credit': 300_000_000_000_000,
                    'gross_credit': 200_000_000_000_000,
                    'lb_shares': 30_000,
                },
            },

            'upfront_commission': 1_500,  # 1.5%
        }

        super().setUpClass(initial_storage, btc_version=True)

        cls.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        cls.tzbtc_token.transfer(**{
            'from': BOB_ADDRESS,
            'to': cls.main_contract.context.address,
            'value': 1_480,
        }).send(gas_reserve=10000, min_confirmations=1)

    def test_basic(self):
        main_address = self.main_contract.context.address
        admin_balance = self.alice_client.balance()
        bob_balance = self.bob_client.balance()

        # DEX storage:
        # tokenPool 10^3
        # xtzPool 10^9
        # lqtTotal 10^6
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 100,  # this makes 90_735_611 xtz
            minXtzBought = 90_000_000,
            amount2Lqt = 250_000_000,  # requires more 303 tzBTC
            minLqtMinted = 270_000,  # 274_974 LB minted
        ).with_amount(204_500_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.main_contract.context.get_balance(), 0)
        self.assertEqual(self.alice_client.balance() - admin_balance, Decimal('4.5'))  # upfront commission
        self.assertAlmostEqual(bob_balance - self.bob_client.balance(), Decimal('204.500_000'), delta=TEST_GAS_DELTA)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 274_974)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 274_974)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 1_124)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 1_124)

        dttm_delta = self.main_contract.storage['index_update_dttm']() - self.initial_now

        expected_gross_credit_index = ceil(1_900_000_000_000 * (1_000_000_000_000 + 2870 * dttm_delta) / 1_000_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), expected_gross_credit_index)

        expected_net_credit_index = ceil(1_600_000_000_000 * (1_000_000_000_000 + 2583 * dttm_delta) / 1_000_000_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), expected_net_credit_index)

        expected_deposit_index = 1_500_000_000_000 * (1_000_000_000_000 + 1928 * dttm_delta) // 1_000_000_000_000
        self.assertEqual(self.main_contract.storage['deposit_index'](), expected_deposit_index)

        # bob's data in liquidity book
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 244_974)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), ceil(1_000 * 10**12 + 356 * 10**24 / expected_gross_credit_index))
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), ceil(1_100 * 10**12 + 356 * 10**24 / expected_net_credit_index))

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), ceil(1_200 * 10**12 + 356 * 10**24 / expected_gross_credit_index))
        self.assertEqual(self.main_contract.storage['total_net_credit'](), ceil(1_400 * 10**12 + 356 * 10**24 / expected_net_credit_index))


class InvestLBFailAbusedLeverageTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'lb_shares': 0,
            'tzBTC_shares': 1_480,

            'deposit_index': 1_500_000_000_000,
            'net_credit_index': 1_600_000_000_000,
            'gross_credit_index': 1_900_000_000_000,

            'total_gross_credit': 1_200_000_000_000_000,
            'total_net_credit': 1_400_000_000_000_000,
            'totalSupply': 2_000_000_000_000_000,

            'upfront_commission': 1_500,  # 1.5%
        }

        super().setUpClass(initial_storage, btc_version=True)

        cls.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        cls.tzbtc_token.transfer(**{
            'from': BOB_ADDRESS,
            'to': cls.main_contract.context.address,
            'value': 1_480,
        }).send(gas_reserve=10000, min_confirmations=1)
        
    def test_fail_abused_leverage(self):
        """
        Abusing return xtz to make bad farm entry
        """
        admin_balance = self.alice_client.balance()
        bob_balance = self.bob_client.balance()

        # DEX storage:
        # tokenPool 10^3
        # xtzPool 10^9
        # lqtTotal 10^6

        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.investLB(
                amount2tzBTC = 0, 
                mintzBTCTokensBought = 0, 
                tzBTC2xtz = 55,
                minXtzBought = 52_031_199,
                amount2Lqt = 100_000_000,
                minLqtMinted = 104_000, 
            ).with_amount(101_500_000).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 55,
            minXtzBought = 52_031_199,
            amount2Lqt = 100_000_000,
            minLqtMinted = 104_000, 
        ).with_amount(52_250_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertAlmostEqual(bob_balance - self.bob_client.balance(), Decimal('52.250_000'), delta=TEST_GAS_DELTA)
        self.assertEqual(self.alice_client.balance() - admin_balance, Decimal('2.25'))
