from copy import deepcopy
from math import ceil
import time

from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE, LINEAR_RATE_PARAMS, CONST_RATE_PARAMS
from ..constants import FIXED_POINT_PRECISION, INITIAL_INDEX_VALUE


class UpdateIndexesEntryUnitTest(LendingContractBaseTestCase):

    def test_rate(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        test_cases = [
            (0, 0, 0, 0),
            (5, 188, 169, 5),
            (10, 377, 339, 23),
            (15, 566, 509, 55),
            (20, 755, 679, 101),
            (25, 944, 849, 152),
            (30, 1133, 1019, 224),
            (35, 1322, 1189, 309),
            (40, 1511, 1359, 407),
            (45, 1699, 1529, 504),
            (50, 1888, 1699, 628),
            (55, 2077, 1869, 766),
            (60, 2266, 2039, 917),
            (65, 2455, 2209, 1060),
            (70, 2644, 2379, 1237),
            (75, 2833, 2549, 1427),
            (80, 3022, 2719, 1631),
            (85, 3022, 2719, 1712),
            (90, 3022, 2719, 1821),
            (95, 7939, 7145, 5072),
            (100, 12857, 11571, 8678),
            (110, 12857, 11571, 9488),
            (120, 12857, 11571, 10413),
        ]
        for percent, expected_debt_rate, expected_utilization_rate, expected_interest_rate in test_cases:
            for is_working in (True, False):
                with self.subTest(f'percent = {percent} is_working = {is_working}'):
                    storage = deepcopy(DEFAULT_STORAGE)
                    storage['liquidity_baking_address'] = liquidity_baking_address
                    storage['fa_tzBTC_address'] = fa_tzBTC_address
                    storage['fa_lb_address'] = fa_lb_address
                    storage['is_working'] = is_working

                    storage['totalSupply'] = 100
                    storage['total_net_credit'] = percent * 3 // 4
                    storage['total_gross_credit'] = percent
                    
                    result = run_code_patched(
                        self.lending_contract.updateIndexes(),
                        amount = 666,
                        balance = 777,
                        storage = storage,
                        now = 1,
                        sender = BOB_ADDRESS,
                    )

                    self.assertEqual(result.storage['gross_credit_index'] - INITIAL_INDEX_VALUE, expected_debt_rate)
                    
                    if is_working:
                        self.assertEqual(result.storage['net_credit_index'] - INITIAL_INDEX_VALUE, expected_utilization_rate)
                        self.assertEqual(result.storage['deposit_index'] - INITIAL_INDEX_VALUE, expected_interest_rate)

                    else:
                        self.assertEqual(result.storage['net_credit_index'] - INITIAL_INDEX_VALUE, 0)
                        self.assertEqual(result.storage['deposit_index'] - INITIAL_INDEX_VALUE, 0)

    def test_indexes(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        storage = deepcopy(DEFAULT_STORAGE)
        storage['liquidity_baking_address'] = liquidity_baking_address
        storage['fa_tzBTC_address'] = fa_tzBTC_address
        storage['fa_lb_address'] = fa_lb_address
        storage['rate_params'] = CONST_RATE_PARAMS

        storage['totalSupply'] = 25
        storage['total_net_credit'] = 17
        storage['total_gross_credit'] = 18

        test_cases = [
            (0, 1_000_000_000_000, 1_000_000_000_000, 1_000_000_000_000),
            (1, 1_000_000_003_022, 1_000_000_002_719, 1_000_000_001_848),
            (2, 1_000_000_006_044, 1_000_000_005_438, 1_000_000_003_696),
            (3, 1_000_000_009_066, 1_000_000_008_157, 1_000_000_005_544),
        ]
        for seconds, expected_debt_rate, expected_utilization_rate, expected_interest_rate in test_cases:
            with self.subTest(seconds):
                result = run_code_patched(
                    self.lending_contract.updateIndexes(),
                    storage = storage,
                    now = seconds,
                    sender = BOB_ADDRESS,
                )

                self.assertEqual(result.storage['gross_credit_index'], expected_debt_rate)
                self.assertEqual(result.storage['net_credit_index'], expected_utilization_rate)
                self.assertEqual(result.storage['deposit_index'], expected_interest_rate)

        with self.subTest('1 approx year'):
            storage = deepcopy(DEFAULT_STORAGE)
            storage['liquidity_baking_address'] = liquidity_baking_address
            storage['fa_tzBTC_address'] = fa_tzBTC_address
            storage['fa_lb_address'] = fa_lb_address
            storage['rate_params'] = CONST_RATE_PARAMS
            dttm_delta = 7 * 24 * 60 * 60
            now = dttm_delta
            for _ in range(52):
                result = run_code_patched(
                    self.lending_contract.updateIndexes(),
                    amount = 0,
                    balance = 50,
                    storage = storage,
                    now = now,
                    sender = BOB_ADDRESS,
                )
                storage = result.storage
                storage['index_update_dttm'] = now
                now += dttm_delta
            self.assertEqual(
                result.storage['gross_credit_index'],
                1_099_608_210_079  # approx (1 + 3022 / 10^12 * 7 * 24 * 60 * 60) ^ 52
            )

    def test_adjusted_utilization(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        for percent in (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100):
            with self.subTest(percent):
                storage = deepcopy(DEFAULT_STORAGE)
                storage['liquidity_baking_address'] = liquidity_baking_address
                storage['fa_tzBTC_address'] = fa_tzBTC_address
                storage['fa_lb_address'] = fa_lb_address
                storage['rate_params'] = LINEAR_RATE_PARAMS

                storage['deposit_index'] = 3 * INITIAL_INDEX_VALUE
                storage['totalSupply'] = 2 * 100

                storage['net_credit_index'] = INITIAL_INDEX_VALUE
                storage['total_net_credit'] = 1

                storage['gross_credit_index'] = INITIAL_INDEX_VALUE
                storage['total_gross_credit'] = 6 * percent

                result = run_code_patched(
                    self.lending_contract.updateIndexes(),
                    storage = storage,
                    now = 1,
                )
                self.assertEqual(
                    result.storage['gross_credit_index'] - INITIAL_INDEX_VALUE,
                    percent * 10_000_000_000,
                )

        for percent in (100, 110, 120):
            with self.subTest(percent):
                storage = deepcopy(DEFAULT_STORAGE)
                storage['liquidity_baking_address'] = liquidity_baking_address
                storage['fa_tzBTC_address'] = fa_tzBTC_address
                storage['fa_lb_address'] = fa_lb_address
                storage['rate_params'] = LINEAR_RATE_PARAMS

                storage['deposit_index'] = 3 * INITIAL_INDEX_VALUE
                storage['totalSupply'] = 2 * 100

                storage['net_credit_index'] = INITIAL_INDEX_VALUE
                storage['total_net_credit'] = 1

                storage['gross_credit_index'] = INITIAL_INDEX_VALUE
                storage['total_gross_credit'] = 6 * percent

                result = run_code_patched(
                    self.lending_contract.updateIndexes(),
                    storage = storage,
                    now = 1,
                )
                self.assertEqual(
                    result.storage['gross_credit_index'] - INITIAL_INDEX_VALUE,
                    1_000_000_000_000,
                )

    def test_utilization(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        # percent is value of utilization in percents

        for percent in (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100):
            with self.subTest(percent):
                storage = deepcopy(DEFAULT_STORAGE)
                storage['liquidity_baking_address'] = liquidity_baking_address
                storage['fa_tzBTC_address'] = fa_tzBTC_address
                storage['fa_lb_address'] = fa_lb_address
                storage['rate_params'] = deepcopy(CONST_RATE_PARAMS)
                storage['rate_params']['rate_1'] = 1_000_000_000_000

                storage['deposit_index'] = INITIAL_INDEX_VALUE
                storage['totalSupply'] = 6 * 100

                storage['net_credit_index'] = 3 * INITIAL_INDEX_VALUE
                storage['total_net_credit'] = 2 * percent

                storage['gross_credit_index'] = INITIAL_INDEX_VALUE
                storage['total_gross_credit'] = 1

                result = run_code_patched(
                    self.lending_contract.updateIndexes(),
                    storage = storage,
                    now = 1,
                )
                self.assertEqual(
                    result.storage['deposit_index'] - INITIAL_INDEX_VALUE,
                    percent * 9_000_000_000,
                )

    def test_update_dttm(self):
        self_address = self.lending_contract.context.get_self_address()
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        storage = deepcopy(DEFAULT_STORAGE)
        storage['liquidity_baking_address'] = liquidity_baking_address
        storage['fa_tzBTC_address'] = fa_tzBTC_address
        storage['fa_lb_address'] = fa_lb_address
        result = run_code_patched(
            self.lending_contract.updateIndexes(),
            amount = 0,
            balance = 0,
            storage = storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        self.assertEqual(result.storage['index_update_dttm'], 0)
        self.assertEqual(len(result.operations), 3)

        # update lqt total
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_lb_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getTotalSupply')
        self.assertEqual(operation['parameters']['value']['args'][0]['prim'], 'Unit')
        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][1]['bytes'], self_address)

        # update tcbtc pool
        operation = result.operations[1]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getBalance')
        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)
        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][1]['bytes'], self_address)

        # calculate lb price
        operation = result.operations[2]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'calculateLbPrice')
        self.assertEqual(operation['parameters']['value']['prim'], 'Unit')

    def test_nonconst_rate_params(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        initial_now = int(time.time())
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['index_update_dttm'] = initial_now

        initial_storage['deposit_index'] = 1_500_000_000_000
        initial_storage['net_credit_index'] = 1_600_000_000_000
        initial_storage['gross_credit_index'] = 1_900_000_000_000

        initial_storage['totalSupply'] = 3_500_000_000_000_000
        initial_storage['total_net_credit'] = 1_400_000_000_000_000
        initial_storage['total_gross_credit'] = 1_200_000_000_000_000
        initial_balance = 1_480_000_000

        # calculate new indexes
        dttm_delta = 21
        utilization = 426_666_666_666
        adjusted_utilization = 434_285_714_285

        debt_rate = 1640
        expected_debt_rate = ceil(1_900_000_000_000 * (1_000_000_000_000 + debt_rate * dttm_delta) / 1_000_000_000_000)

        utilization_rate = debt_rate * 9 // 10
        expected_utilization_rate = ceil(1_600_000_000_000 * (1_000_000_000_000 + utilization_rate * dttm_delta) / 1_000_000_000_000)

        interest_rate = utilization_rate * utilization // 1_000_000_000_000
        expected_interest_rate = 1_500_000_000_000 * (1_000_000_000_000 + interest_rate * dttm_delta) // 1_000_000_000_000

        result = run_code_patched(
            self.lending_contract.updateIndexes(),
            amount = 0,
            balance = initial_balance,
            storage = initial_storage,
            now = initial_now + dttm_delta,
            sender = BOB_ADDRESS,
        )

        self.assertEqual(result.storage['gross_credit_index'], expected_debt_rate)
        self.assertEqual(result.storage['net_credit_index'], expected_utilization_rate)
        self.assertEqual(result.storage['deposit_index'], expected_interest_rate)
