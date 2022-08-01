import time
from math import ceil
from decimal import Decimal

from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...tzbtc_invest_params import get_invest_params, get_client_invest_params
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class InvestLeverageGreater2Test(MainContractBaseTestCase):
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
        super().setUpClass(initial_storage, btc_version=True)

    def test_leverage_greater_than_2(self):
        # Bob deposits 0.1 BTC
        self.bob_client.bulk(
            self.tzbtc_token.approve(value = 10**7, spender = self.main_contract.address),
            self.main_contract.depositLending(10**7),
        ).send(gas_reserve=10000, min_confirmations=1)

        # xtz/tzbtc = 10^-8, mutez/satoshi = 10^-6

        amount, xtz2token, tokens, tzBTC2xtz, minXtzBought, xtz2lqt, lqtMinted = get_invest_params(
            self.dex_contract.storage['tokenPool'](),  # 1_000
            self.dex_contract.storage['xtzPool'](), # 1_000_000_000
            self.dex_contract.storage['lqtTotal'](),  # 1_000_000,
            30_000_000,
            40, # leverage ~2.33
            2,
        )
        # params 30759045 0 0 5 4965202 33976115 34145
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            tzBTC2xtz = tzBTC2xtz,
            minXtzBought = minXtzBought,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0.759044'),  # upfront commission
        )
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS](), {
            'gross_credit': 40_000_000,
            'lb_shares': 34145,
            'net_credit': 40_000_000_000,
        })


class ClientInvestParamsLeverageGreater2Test(MainContractBaseTestCase):
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
        super().setUpClass(initial_storage, btc_version=True)

    def test_leverage_greater_than_2(self):
        # Bob deposits 0.1 BTC
        self.bob_client.bulk(
            self.tzbtc_token.approve(value = 10**7, spender = self.main_contract.address),
            self.main_contract.depositLending(10**7),
        ).send(gas_reserve=10000, min_confirmations=1)

        # xtz/tzbtc = 10^-8, mutez/satoshi = 10^-6

        amount, xtz2token, tokens, tzBTC2xtz, minXtzBought, xtz2lqt, lqtMinted = get_client_invest_params(
            self.dex_contract.storage['tokenPool'](),  # 1_000
            self.dex_contract.storage['xtzPool'](), # 1_000_000_000
            self.dex_contract.storage['lqtTotal'](),  # 1_000_000,
            30_000_000,
            2.3,
            2,
        )
        # params 30000000 0 0 4 3976114 33231944 33364
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            tzBTC2xtz = tzBTC2xtz,
            minXtzBought = minXtzBought,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0.744160'),  # upfront commission
        )
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS](), {
            'gross_credit': 38_000_000,
            'lb_shares': 33364,
            'net_credit': 38_000_000_000,
        })


class InvestLeverageLess2Test(MainContractBaseTestCase):
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
        super().setUpClass(initial_storage, btc_version=True)

    def test_leverage_less_than_2(self):
        # Bob deposits 0.1 BTC
        self.bob_client.bulk(
            self.tzbtc_token.approve(value = 10**7, spender = self.main_contract.address),
            self.main_contract.depositLending(10**7),
        ).send(gas_reserve=10000, min_confirmations=1)

        # xtz/tzbtc = 10^-8, mutez/satoshi = 10^-6

        amount, xtz2token, tokens, tzBTC2xtz, minXtzBought, xtz2lqt, lqtMinted = get_invest_params(
            self.dex_contract.storage['tokenPool'](),  # 1_000
            self.dex_contract.storage['xtzPool'](), # 1_000_000_000
            self.dex_contract.storage['lqtTotal'](),  # 1_000_000,
            300_000_000,
            100, # leverage ~1.33
            2,
        )
        # params 302468942 88276434 80 0 0 211723566 194565

        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            tzBTC2xtz = tzBTC2xtz,
            minXtzBought = minXtzBought,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('2.468942'),  # upfront commission
        )
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS](), {
            'gross_credit': 100_000_000,
            'lb_shares': 194_565,
            'net_credit': 100_000_000_000,
        })

class ClientInvestParamsLeverageLess2Test(MainContractBaseTestCase):
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
        super().setUpClass(initial_storage, btc_version=True)

    def test_leverage_less_than_2(self):
        # Bob deposits 0.1 BTC
        self.bob_client.bulk(
            self.tzbtc_token.approve(value = 10**7, spender = self.main_contract.address),
            self.main_contract.depositLending(10**7),
        ).send(gas_reserve=10000, min_confirmations=1)

        # xtz/tzbtc = 10^-8, mutez/satoshi = 10^-6

        amount, xtz2token, tokens, tzBTC2xtz, minXtzBought, xtz2lqt, lqtMinted = get_client_invest_params(
            self.dex_contract.storage['tokenPool'](),  # 1_000
            self.dex_contract.storage['xtzPool'](), # 1_000_000_000
            self.dex_contract.storage['lqtTotal'](),  # 1_000_000,
            30_000_000,
            1.5,
            2,
        )
        # params 30000000 7425762 7 0 0 22277210 22113
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            tzBTC2xtz = tzBTC2xtz,
            minXtzBought = minXtzBought,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0.297028'),  # upfront commission
        )
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS](), {
            'gross_credit': 15_000_000,
            'lb_shares': 22_113,
            'net_credit': 15_000_000_000,
        })


class ClientInvestParamsLeverageOneTest(MainContractBaseTestCase):
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
        super().setUpClass(initial_storage, btc_version=True)

    def test_leverage_one(self):
        # Bob deposits 0.1 BTC
        self.bob_client.bulk(
            self.tzbtc_token.approve(value = 10**7, spender = self.main_contract.address),
            self.main_contract.depositLending(10**7),
        ).send(gas_reserve=10000, min_confirmations=1)

        # xtz/tzbtc = 10^-8, mutez/satoshi = 10^-6

        amount, xtz2token, tokens, tzBTC2xtz, minXtzBought, xtz2lqt, lqtMinted = get_client_invest_params(
            self.dex_contract.storage['tokenPool'](),  # 1_000
            self.dex_contract.storage['xtzPool'](), # 1_000_000_000
            self.dex_contract.storage['lqtTotal'](),  # 1_000_000,
            30_000_000,
            1,
            2,
        )
        # params 30000000 15565783 15 0 0 14434217 14213
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            tzBTC2xtz = tzBTC2xtz,
            minXtzBought = minXtzBought,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0'),  # upfront commission
        )
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS](), {
            'gross_credit': 0,
            'lb_shares': 14213,
            'net_credit': 0,
        })

class ClientInvestParamsLeverageAlmostOneTest(MainContractBaseTestCase):
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
        super().setUpClass(initial_storage, btc_version=True)

    def test_leverage_almost_one(self):
        # Bob deposits 0.1 BTC
        self.bob_client.bulk(
            self.tzbtc_token.approve(value = 10**7, spender = self.main_contract.address),
            self.main_contract.depositLending(10**7),
        ).send(gas_reserve=10000, min_confirmations=1)

        # xtz/tzbtc = 10^-8, mutez/satoshi = 10^-6

        amount, xtz2token, tokens, tzBTC2xtz, minXtzBought, xtz2lqt, lqtMinted = get_client_invest_params(
            self.dex_contract.storage['tokenPool'](),  # 1_000
            self.dex_contract.storage['xtzPool'](), # 1_000_000_000
            self.dex_contract.storage['lqtTotal'](),  # 1_000_000,
            30_000_000,
            1.0001,
            2,
        )
        # params 30000000 14998497 14 0 0 15001445 14779
        admin_balance = self.alice_client.balance()
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            tzBTC2xtz = tzBTC2xtz,
            minXtzBought = minXtzBought,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
        ).with_amount(amount).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(
            self.alice_client.balance() - admin_balance,
            Decimal('0.000058'),  # upfront commission
        )
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS](), {
            'gross_credit': 1_000_000,
            'lb_shares': 14779,
            'net_credit': 1_000_000_000,
        })
