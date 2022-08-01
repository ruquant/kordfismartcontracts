import time
from math import ceil
from decimal import Decimal

from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...xtz_invest_params import get_client_invest_params
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
            'deposit_index': 10**12,
            'net_credit_index': 10**15,
            'gross_credit_index': 10**18,
            'upfront_commission': 2_000,
        }
        super().setUpClass(initial_storage)

    def test_leverage_greater_than_2(self):
        main_address = self.main_contract.context.address
        # Bob deposits 200 xtz
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending().with_amount(2 * 10**8).send(gas_reserve=10000, min_confirmations=1)

        amount, xtz2token, tokens, xtz2lqt, lqtMinted = get_client_invest_params(
            tokenPool = 1_000,
            xtzPool = 1_000_000_000,
            lqtTotal = 1_000_000,
            xtz_invest = 30_000_000,
            leverage = 3.2,
            commission = 2,
        )
        # params 30000000, 45022080 43 45861063 43887
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
            tzBTCShares = 0,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('1.242513'),  # upfront commission
        )
        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 43_887)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 43_887)

        self.assertEqual(self.main_contract.context.get_balance(), 137_874_344)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 62_125_656)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 62_125_656_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 43_887)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 62_125_656)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 62_125_656_000)


class InvestLeverageOneTest(MainContractBaseTestCase):
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
            'upfront_commission': 2_000,
        }
        super().setUpClass(initial_storage)

    def test_leverage_one(self):
        main_address = self.main_contract.context.address
        # Bob deposits 200 xtz
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending().with_amount(2 * 10**8).send(gas_reserve=10000, min_confirmations=1)

        amount, xtz2token, tokens, xtz2lqt, lqtMinted = get_client_invest_params(
            tokenPool = 1_000,
            xtzPool = 1_000_000_000,
            lqtTotal = 1_000_000,
            xtz_invest = 30_000_000,
            leverage = 1,
            commission = 2,
        )
        # params 29688790 15258930 15 14429860 14213
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
            tzBTCShares = 0,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0'),  # upfront commission
        )
        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 14_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 14_213)

        self.assertEqual(self.main_contract.context.get_balance(), 200_000_000)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 14_213)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)


class InvestLeverageAlmostOneTest(MainContractBaseTestCase):
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
            'upfront_commission': 2_000,
        }
        super().setUpClass(initial_storage)

    def test_leverage_almost_one(self):
        main_address = self.main_contract.context.address
        # Bob deposits 200 xtz
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending().with_amount(2 * 10**8).send(gas_reserve=10000, min_confirmations=1)

        amount, xtz2token, tokens, xtz2lqt, lqtMinted = get_client_invest_params(
            tokenPool = 1_000,
            xtzPool = 1_000_000_000,
            lqtTotal = 1_000_000,
            xtz_invest = 30_000_000,
            leverage = 1.01,
            commission = 2,
        )
        # params 29688790 15258930 15 14429860 14213
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
            tzBTCShares = 0,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0'),  # upfront commission
        )
        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 14_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 14_213)

        self.assertEqual(self.main_contract.context.get_balance(), 200_000_000)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 14_213)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)
