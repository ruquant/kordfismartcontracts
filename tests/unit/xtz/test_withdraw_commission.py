from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched, LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE


class WithdrawCommissionEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address

        # case normal
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['gross_credit_index'] = 1_500_000_000_000
        initial_storage['total_gross_credit'] = 2_000_000_000_000
        initial_storage['deposit_index'] = 500_000_000_000
        initial_storage['totalSupply'] = 4_000_000_000_000

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            balance = 1_000_000,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 1_000_000)
        self.assertEqual(operation['destination'], ALICE_ADDRESS)

        self.assertDictEqual(new_storage, initial_storage)

        # another normal case
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['gross_credit_index'] = 1_500_000_000_000
        initial_storage['total_gross_credit'] = 2_000_000_000_000
        initial_storage['deposit_index'] = 500_000_000_000
        initial_storage['totalSupply'] = 8_000_000_000_000

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            balance = 4_000_000,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 3_000_000)
        self.assertEqual(operation['destination'], ALICE_ADDRESS)

        self.assertDictEqual(new_storage, initial_storage)

        # case small amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['gross_credit_index'] = 1_500_000_500_000
        initial_storage['total_gross_credit'] = 2_000_000_000_000
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 2_000_000_000_000

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            balance = 1_000_000,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 1)
        self.assertEqual(operation['destination'], ALICE_ADDRESS)

        self.assertDictEqual(new_storage, initial_storage)

    def test_negative_values(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address

        # case zero
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['gross_credit_index'] = 1_500_000_000_000
        initial_storage['total_gross_credit'] = 2_000_000_000_000
        initial_storage['deposit_index'] = 1_000_000_000_000
        initial_storage['totalSupply'] = 4_000_000_000_000

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            balance = 1_000_000,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(new_storage, initial_storage)

        # case negative
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['gross_credit_index'] = 1_500_000_000_000
        initial_storage['total_gross_credit'] = 2_000_000_000_000
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 5_000_000_000_000

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            balance = 1_000_000,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(new_storage, initial_storage)

        # case positive but mutez amount zero
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['gross_credit_index'] = 1_500_000_499_999
        initial_storage['total_gross_credit'] = 2_000_000_000_000
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 2_000_000_000_000

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            balance = 1_000_000,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(new_storage, initial_storage)

    def test_forbidden_case(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            storage['liquidity_baking_address'] = liquidity_baking_address
            storage['fa_tzBTC_address'] = fa_tzBTC_address
            storage['fa_lb_address'] = fa_lb_address
            self.lending_contract.withdrawCommission().run_code(storage=storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

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
            self.lending_contract.withdrawCommission(),
            amount = 0,
            balance = 0,
            storage = storage,
            now = 107,
            sender = ALICE_ADDRESS,
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
