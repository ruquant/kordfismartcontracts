import time
from decimal import Decimal
from copy import deepcopy
from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError

from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


INITIAL_STORAGE = {
    'index_update_dttm': int(time.time()),
    'deposit_index': 1_500_000_000_000,
    'net_credit_index': 1_600_000_000_000,
    'gross_credit_index': 1_900_000_000_000,
    'total_gross_credit': 1_220_000_000_000_000,
    'total_net_credit': 1_360_000_000_000_000,
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
            'gross_credit': 1_000_000_000_000_000, # ~ $380
            'lb_shares': 100_000,  # ~ $200
        },
        CLARE_ADDRESS: {
            'net_credit': 230_000_000_000_000,
            'gross_credit': 200_000_000_000_000, # ~ $760
            'lb_shares': 250_000,  # ~ $500
        },
        ALICE_ADDRESS: {
            'net_credit': 30_000_000_000_000,
            'gross_credit': 20_000_000_000_000, # ~ $76
            'lb_shares': 60_000,  # ~ $120
        },
    },
    'lb_shares': 410_000,
    'upfront_commission': 10000,
    'is_working': True,
}


class LiquidateNormalEntryTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        initial_storage = deepcopy(INITIAL_STORAGE)
        initial_storage['index_update_dttm'] = int(time.time())
        initial_storage['lb_price'] = 1_000_000_000
        initial_amount = 1_480_000_000
        super().setUpClass(initial_storage, initial_amount)
        transfer_params = {
            'from': ALICE_ADDRESS,
            'to': cls.main_contract.context.address,
            'value': 410_000,
        }
        cls.alice_client.bulk(
            cls.lqt_token.transfer(**transfer_params),
            cls.oracle.set_price(2_000_000, 100_000_000_000_000),
        ).send(gas_reserve=10000, min_confirmations=1) 

    def test_liquidate(self):
        # Can liquidate Clare entry
        initial_now = self.main_contract.storage['index_update_dttm']()
        initial_admin_balance = self.alice_client.balance()
        initial_bob_balance = self.bob_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .liquidateLB(CLARE_ADDRESS)
            .with_amount(418_000_000 + int(time.time() - initial_now))
            .send(gas_reserve=10000, min_confirmations=1))

        self.assertEqual(self.main_contract.storage['local_params']['tzbtc_pool'](), 1_000)
        self.assertEqual(self.main_contract.storage['local_params']['lqt_total'](), 1_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 160_000)
        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_020_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_130_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)
        self.assertAlmostEqual(self.main_contract.storage['deposit_index'](), 1_504_750_016_000, delta=10_000)
        self.assertAlmostEqual(self.main_contract.storage['net_credit_index'](), 1_600_000_046_000, delta=15_000)
        self.assertAlmostEqual(self.main_contract.storage['gross_credit_index'](), 1_900_000_061_000, delta=20_000)

        self.assertEqual(self.lqt_token.storage['tokens'][BOB_ADDRESS](), 250_000)
        self.assertAlmostEqual(self.alice_client.balance() - initial_admin_balance, Decimal('19.000_001'), delta=Decimal('0.00001'))


class PartialLiquidationTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        initial_storage = deepcopy(INITIAL_STORAGE)
        initial_storage['index_update_dttm'] = int(time.time())
        initial_storage['lb_price'] = 1_000_000_000
        initial_storage['rate_params'] = {
            'rate_1': 0,
            'rate_diff': 0,
            'threshold_percent_1': 0,
            'threshold_percent_2': 100,
        }
        initial_amount = 1_480_000_000
        super().setUpClass(initial_storage, initial_amount)
        transfer_params = {
            'from': ALICE_ADDRESS,
            'to': cls.main_contract.context.address,
            'value': 410_000,
        }
        cls.alice_client.bulk(
            cls.lqt_token.transfer(**transfer_params),
            cls.oracle.set_price(2_000_000, 100_000_000_000_000),
        ).send(gas_reserve=10000, min_confirmations=1) 

    def test_partial_liquidation(self):
        # Can partially liquidate Clare entry
        initial_admin_balance = self.alice_client.balance()
        initial_bob_balance = self.bob_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .liquidateLB(CLARE_ADDRESS)
            .with_amount(110_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        self.assertEqual(self.main_contract.storage['local_params']['tzbtc_pool'](), 1_000)
        self.assertEqual(self.main_contract.storage['local_params']['lqt_total'](), 1_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 147_368_421_052_632)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 169_473_684_210_527)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 184_211)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 344_211)
        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_167_368_421_052_632)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_299_473_684_210_527)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_501_250_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_600_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 1_900_000_000_000)

        self.assertEqual(self.lqt_token.storage['tokens'][BOB_ADDRESS](), 65_789)
        self.assertAlmostEqual(self.alice_client.balance() - initial_admin_balance, Decimal('5.000_001'), delta=Decimal('0.00001'))

        # Can liquidate remainder
        initial_admin_balance = self.alice_client.balance()
        initial_bob_balance = self.bob_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .liquidateLB(CLARE_ADDRESS)
            .with_amount(308_000_015)
            .send(gas_reserve=10000, min_confirmations=1))

        self.assertEqual(self.main_contract.storage['local_params']['tzbtc_pool'](), 1_000)
        self.assertEqual(self.main_contract.storage['local_params']['lqt_total'](), 1_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 160_000)
        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_020_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_130_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_504_750_000_250)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_600_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 1_900_000_000_000)

        self.assertEqual(self.lqt_token.storage['tokens'][BOB_ADDRESS](), 250_000)
        self.assertAlmostEqual(self.alice_client.balance() - initial_admin_balance, Decimal('14.000_001'), delta=Decimal('0.00001'))
