from datetime import datetime, timedelta
from decimal import Decimal

from pytezos.crypto.key import Key
from .constants import BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, TEST_GAS_DELTA
from .base import DemoLBBaseTestCase


class DemoLBTest(DemoLBBaseTestCase):

    def test_add_n_remove_liquidity(self):
        initial_bob_balance = self.bob_client.balance()

        # Bob transfers all his tokens to Clare.
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.transfer(**{
            'from': BOB_ADDRESS,
            'to': CLARE_ADDRESS,
            'value': 100_000_000,
        }).send(gas_reserve=10000, min_confirmations=1)

        # Bob buys tzBTC tokens
        xtz_to_token_params = {
            'to': BOB_ADDRESS,
            'minTokensBought': 0,
            'deadline': int((datetime.now() + timedelta(minutes=1)).timestamp()),
        }
        # TODO: `.using(key=BOB_KEY)` not working with contract address set
        self.dex_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (
            self.dex_contract
                # .using(key=BOB_KEY)
                .xtzToToken(**xtz_to_token_params)
                .with_amount(10 ** 7)
                .send(gas_reserve=10000, min_confirmations=1)
        )

        bob_tzbtc_tokens = self.tzbtc_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_tzbtc_tokens, 9)
        bob_balance = self.bob_client.balance()
        self.assertAlmostEqual(initial_bob_balance - bob_balance, Decimal('10'), delta=TEST_GAS_DELTA)

        # addLiquidity test
        # Bob adds liquidity
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            spender=self.dex_contract.context.address,
            value=9,
        ).send(gas_reserve=10000, min_confirmations=1)

        add_liquidity_params = {
            'owner': BOB_ADDRESS,
            'minLqtMinted': 0,
            'maxTokensDeposited': 9,
            'deadline': int((datetime.now() + timedelta(minutes=1)).timestamp()),
        }
        self.dex_contract.addLiquidity(**add_liquidity_params).with_amount(7 * 10 ** 6).send(gas_reserve=10000, min_confirmations=1)

        spent_xtz = bob_balance - self.bob_client.balance()
        self.assertAlmostEqual(spent_xtz, Decimal('7'), delta=TEST_GAS_DELTA)
        bob_tzbtc_tokens = self.tzbtc_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_tzbtc_tokens, 2)
        bob_lqt_tokens = self.lqt_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_lqt_tokens, 6930)

        # removeLiquidity test
        # Bob removes liquidity
        bob_balance = self.bob_client.balance()

        remove_liquidity_params = {
            'to': BOB_ADDRESS,
            'lqtBurned': 3000,
            'minXtzWithdrawn': 0,
            'minTokensWithdrawn': 0,
            'deadline': int((datetime.now() + timedelta(minutes=1)).timestamp()),
        }
        self.dex_contract.removeLiquidity(**remove_liquidity_params).send(gas_reserve=10000, min_confirmations=1)

        bob_lqt_tokens = self.lqt_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_lqt_tokens, 3930)

        got_xtz = self.bob_client.balance() - bob_balance
        self.assertAlmostEqual(got_xtz, Decimal('3'), delta=TEST_GAS_DELTA)
        
        bob_tzbtc_tokens = self.tzbtc_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_tzbtc_tokens, 4)
