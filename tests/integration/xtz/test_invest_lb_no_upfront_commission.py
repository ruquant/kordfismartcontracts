import time
from math import ceil
from fractions import Fraction

from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...xtz_invest_params import get_invest_params
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class InvestLeverageNoUpfrontCommissionTest(MainContractBaseTestCase):
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

            # no upfront commission
            'upfront_commission': 0,
        }
        super().setUpClass(initial_storage, btc_version=False)

    def test_different_leverages(self):
        main_address = self.main_contract.context.address

        # Bob deposits 200 xtz
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending().with_amount(2 * 10**8).send(gas_reserve=10000, min_confirmations=1)

        # Bob invest LB leverage up to 1.5
        xtz2token, tokens, xtz2lqt, lqtMinted = get_invest_params(
            tokenPool = 1_000,
            xtzPool = 1_000_000_000,
            lqtTotal = 1_000_000,
            invest_amount = 30_000_000,
        )
        # xtz2token + xtz2lqt = 29_688_790
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
            tzBTCShares = 0,
        ).with_amount(20_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 14_213)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 14_213)

        self.assertEqual(self.main_contract.context.get_balance(), 190_311_210)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 9_688_790)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 9_688_790_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 14_213)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 9_688_790)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 9_688_790_000)

        # Bob invest LB leverage up to 2
        xtz2token, tokens, xtz2lqt, lqtMinted = get_invest_params(
            tokenPool = 1_000,
            xtzPool = 1_029_673_531,
            lqtTotal = 1_014_213,
            invest_amount = 30_000_000,
        )
        # xtz2token + xtz2lqt = 28_940_342
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
            tzBTCShares = 0,
        ).with_amount(15_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 27_584)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 27_584)

        self.assertEqual(self.main_contract.context.get_balance(), 176_370_868)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 23_629_132)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 23_629_132_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 27_584)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 23_629_132)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 23_629_132_000)

        # Bob invest LB leverage up to 3.99
        xtz2token, tokens, xtz2lqt, lqtMinted = get_invest_params(
            tokenPool = 1_000,
            xtzPool = 1_058_598_708,
            lqtTotal = 1_027_584,
            invest_amount = 30_000_000,
        )
        # xtz2token + xtz2lqt = 29_216_479
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = xtz2token,
            mintzBTCTokensBought = tokens,
            amount2Lqt = xtz2lqt,
            minLqtMinted = lqtMinted,
            tzBTCShares = 0,
        ).with_amount(7_518_797).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 41_132)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 41_132)

        self.assertEqual(self.main_contract.context.get_balance(), 154_673_186)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 45_326_814)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 45_326_814_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 41_132)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 45_326_814)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 45_326_814_000)

        # Bob invest LB leverage = 4.01
        xtz2token, tokens, xtz2lqt, lqtMinted = get_invest_params(
            tokenPool = 1_000,
            xtzPool = 1_087_800_126,
            lqtTotal = 1_041_132,
            invest_amount = 30_000_000,
        )
        # xtz2token + xtz2lqt = 28_882_216
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.investLB(
                amount2tzBTC = xtz2token,
                mintzBTCTokensBought = tokens,
                amount2Lqt = xtz2lqt,
                minLqtMinted = lqtMinted,
                tzBTCShares = 0,
            ).with_amount(7_202_548).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')


class InvestLBWithIndexesTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial_now = int(time.time()) - 60 * 60 * 24 * 7  # week ago
        initial_storage = {}
        initial_storage['index_update_dttm'] = cls.initial_now
        initial_storage['deposit_index'] = 1_500_000_000_000
        initial_storage['net_credit_index'] = 1_600_000_000_000
        initial_storage['gross_credit_index'] = 1_900_000_000_000
        initial_storage['total_gross_credit'] = 1_200_000_000_000_000
        initial_storage['total_net_credit'] = 1_400_000_000_000_000
        initial_storage['totalSupply'] = 3_500_000_000_000_000
        initial_storage['ledger'] = {
            BOB_ADDRESS: {
                'balance': 2_000_000_000_000_000,
                'approvals': {},
            },
            CLARE_ADDRESS: {
                'balance': 2_000_000_000_000_000,
                'approvals': {},
            },
        }
        initial_storage['liquidity_book'] = {
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
        }
        initial_storage['lb_shares'] = 130_000
        initial_amount = 1_480_000_000

        initial_storage['upfront_commission'] = 0
        super().setUpClass(initial_storage, initial_amount)

    def test_invest(self):
        invest_params = get_invest_params(
            self.dex_contract.storage['tokenPool'](),
            self.dex_contract.storage['xtzPool'](),
            self.dex_contract.storage['lqtTotal'](),
            500_000_000,
        )
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .investLB(*invest_params, 0)
            .with_amount(250_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        # calculate new indexes
        dttm_delta = self.main_contract.storage['index_update_dttm']() - self.initial_now
        utilization = 426_666_666_666
        adjusted_utilization = 434_285_714_285

        debt_rate = 1640
        # TODO: should be ceil rounding? https://trello.com/c/Ohz1B6eD
        expected_gross_credit_index = ceil(1_900_000_000_000 * (1_000_000_000_000 + debt_rate * dttm_delta) / 1_000_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), expected_gross_credit_index)

        utilization_rate = debt_rate * 9 // 10
        expected_net_credit_index = ceil(1_600_000_000_000 * (1_000_000_000_000 + utilization_rate * dttm_delta) / 1_000_000_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), expected_net_credit_index)

        interest_rate = utilization_rate * utilization // 1_000_000_000_000
        expected_deposit_index = 1_500_000_000_000 * (1_000_000_000_000 + interest_rate * dttm_delta) // 1_000_000_000_000
        self.assertEqual(self.main_contract.storage['deposit_index'](), expected_deposit_index)
        
        balance_delta = (1_480_000_000 - self.main_contract.context.get_balance()) * 1_000_000
        self.assertEqual(balance_delta, 248_500_227_000_000)

        # check bob entry
        expected_bob_net_credit = ceil(1_100_000_000_000_000 + Fraction(balance_delta * 1_000_000_000_000, expected_net_credit_index))
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), expected_bob_net_credit)
        expected_bob_gross_credit = ceil(1_000_000_000_000_000 + Fraction(balance_delta * 1_000_000_000_000, expected_gross_credit_index))
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), expected_bob_gross_credit)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 192_766)

        # check total utilization and debt
        self.assertEqual(
            self.main_contract.storage['total_net_credit'](),
            ceil(1_400_000_000_000_000 + Fraction(balance_delta * 1_000_000_000_000, expected_net_credit_index)),
        )
        self.assertEqual(
            self.main_contract.storage['total_gross_credit'](),
            ceil(1_200_000_000_000_000 + Fraction(balance_delta * 1_000_000_000_000, expected_gross_credit_index)),
        )
        self.assertEqual(self.main_contract.storage['lb_shares'](), 222_766)


class InvestLBWithIndexeAndDisabledFlagsTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial_now = int(time.time()) - 60 * 60 * 24 * 7  # week ago
        initial_storage = {
            'index_update_dttm': cls.initial_now,
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
            'lb_shares': 130_000,
            'upfront_commission': 0,
            'is_working': False,
        }
        initial_amount = 1_480_000_000
        super().setUpClass(initial_storage, initial_amount)

    def test_invest(self):
        invest_params = get_invest_params(
            self.dex_contract.storage['tokenPool'](),
            self.dex_contract.storage['xtzPool'](),
            self.dex_contract.storage['lqtTotal'](),
            500_000_000,
        )
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        (self.main_contract
            .investLB(*invest_params, 0)
            .with_amount(250_000_000)
            .send(gas_reserve=10000, min_confirmations=1))

        debt_rate = 2870
        dttm_delta = self.main_contract.storage['index_update_dttm']() - self.initial_now

        expected_gross_credit_index = ceil(1_900_000_000_000 * (1_000_000_000_000 + debt_rate * dttm_delta) / 1_000_000_000_000)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), expected_gross_credit_index)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_600_000_000_000)
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_500_000_000_000)

        balance_delta = (1_480_000_000 - self.main_contract.context.get_balance()) * 1_000_000
        self.assertEqual(balance_delta, 248_500_227_000_000)

        # check bob entry
        expected_bob_net_credit = 1_100_000_000_000_000 + balance_delta * 1_000_000_000_000 // 1_600_000_000_000
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), expected_bob_net_credit)
        expected_bob_gross_credit = ceil(1_000_000_000_000_000 + Fraction(balance_delta * 1_000_000_000_000, expected_gross_credit_index))
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), expected_bob_gross_credit)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 192_766)

        # check total utilization and debt
        self.assertEqual(
            self.main_contract.storage['total_net_credit'](),
            1_400_000_000_000_000 + balance_delta * 1_000_000_000_000 // 1_600_000_000_000,
        )
        self.assertEqual(
            self.main_contract.storage['total_gross_credit'](),
            ceil(1_200_000_000_000_000 + Fraction(balance_delta * 1_000_000_000_000, expected_gross_credit_index)),
        )
        self.assertEqual(self.main_contract.storage['lb_shares'](), 222_766)
