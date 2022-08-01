from copy import deepcopy
import time
from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class CalculateLbPriceUnitTest(LendingContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_max_one_day_change(self):
        self_address = self.lending_contract.context.get_self_address()

        # price lowers more than 50% in a day
        storage = deepcopy(DEFAULT_STORAGE)
        storage['lb_price'] = 1_000_000_000_000
        storage['local_params']['lqt_total'] = 3_000_000
        storage['local_params']['tzbtc_pool'] = 2_000
        result = run_code_patched(
            self.lending_contract.calculateLbPrice(),
            amount = 666,
            balance = 777,
            storage = storage,
            now = 86400,  # one day
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['lb_price'], 500_003_200_000)
        self.assertEqual(new_storage['index_update_dttm'], 86400)

        # price grows more than 50% in a day
        storage = deepcopy(DEFAULT_STORAGE)
        storage['lb_price'] = 1_000
        storage['local_params']['lqt_total'] = 3_000_000
        storage['local_params']['tzbtc_pool'] = 2_000
        result = run_code_patched(
            self.lending_contract.calculateLbPrice(),
            amount = 666,
            balance = 777,
            storage = storage,
            now = 86400,  # one day
            sender = self_address,
        )

        new_storage = deepcopy(result.storage)
        self.assertEqual(new_storage['lb_price'], 1_499)
        self.assertEqual(new_storage['index_update_dttm'], 86400)

        # price changes less than 50%
        storage = deepcopy(DEFAULT_STORAGE)
        storage['lb_price'] = 1_000_000_000
        storage['local_params']['lqt_total'] = 3_000_000
        storage['local_params']['tzbtc_pool'] = 2_000
        result = run_code_patched(
            self.lending_contract.calculateLbPrice(),
            amount = 666,
            balance = 777,
            storage = storage,
            now = 86400,  # one day
            sender = self_address,
        )

        new_storage = deepcopy(result.storage)
        self.assertEqual(new_storage['lb_price'], 666_666_666)
        self.assertEqual(new_storage['index_update_dttm'], 86400)


    def test_real_price(self):
        self_address = self.lending_contract.context.get_self_address()

        storage = deepcopy(DEFAULT_STORAGE)
        storage['lb_price'] = 100_000_000_000_000
        storage['local_params']['lqt_total'] = 289_769_795
        storage['local_params']['tzbtc_pool'] = 33_756_003_009
        result = run_code_patched(
            self.lending_contract.calculateLbPrice(),
            amount = 666,
            balance = 777,
            storage = storage,
            now = 86400,  # one day
            sender = self_address,
        )

        new_storage = deepcopy(result.storage)
        self.assertEqual(new_storage['lb_price'], 116_492_483_314_211)
        self.assertEqual(new_storage['index_update_dttm'], 86400)

    def test_first_update_reach_lb_price(self):
        self_address = self.lending_contract.context.get_self_address()

        storage = deepcopy(DEFAULT_STORAGE)
        storage['local_params']['lqt_total'] = 289_769_795
        storage['local_params']['tzbtc_pool'] = 33_756_003_009
        result = run_code_patched(
            self.lending_contract.calculateLbPrice(),
            amount = 666,
            balance = 777,
            storage = storage,
            now = int(time.time()),
            sender = self_address,
        )

        new_storage = deepcopy(result.storage)
        self.assertEqual(new_storage['lb_price'], 116_492_483_314_211)
