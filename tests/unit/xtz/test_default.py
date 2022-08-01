from copy import deepcopy


from ..base import LendingContractBaseTestCase, LendingContractBaseTestCase, run_code_patched
from ..constants import BOB_ADDRESS, CONTRACT_ADDRESS, DEFAULT_STORAGE


class DefaultEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = run_code_patched(
            self.lending_contract.default(),
            amount = 10 ** 6,
            balance = 0,
            storage = initial_storage,
            now = 1,
            sender = BOB_ADDRESS,
        )

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(result.storage, initial_storage)

    def test_do_nothing_cases(self):
        # zero total deposit
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['totalSupply'] = 0

        result = run_code_patched(
            self.lending_contract.default(),
            amount = 10 ** 6,
            balance = 0,
            storage = initial_storage,
            now = 1,
            sender = BOB_ADDRESS,
        )

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(result.storage, initial_storage)

        # dex contract call
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = CONTRACT_ADDRESS
        initial_storage['totalSupply'] = 10**12

        result = run_code_patched(
            self.lending_contract.default(),
            amount = 10 ** 6,
            balance = 0,
            storage = initial_storage,
            now = 1,
            sender = CONTRACT_ADDRESS,
        )

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(result.storage, initial_storage)


class DefaultEntrypointWithUpdateTestCase(LendingContractBaseTestCase):
    def test_non_zero_case(self):
        self_address = self.lending_contract.context.get_self_address()
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['totalSupply'] = 1_234_567_890_666
        initial_storage['deposit_index'] = 1_222_333_444_555

        result = run_code_patched(
            self.lending_contract.default(),
            amount = 7 * 10 ** 6,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = result.storage

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

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertEqual(new_storage['totalSupply'], 1_234_567_890_666)
        self.assertEqual(new_storage['deposit_index'], 6_892_333_493_093)
