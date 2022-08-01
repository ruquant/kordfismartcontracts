from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class WithdrawCommissionEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
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

        initial_storage['tzBTC_shares'] = 1

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 1)

        # transfer tzBTC
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], ALICE_ADDRESS)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 1)  # value

        self.assertEqual(new_storage['tzBTC_shares'], 0)
        del initial_storage['tzBTC_shares']
        del new_storage['tzBTC_shares']
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

        initial_storage['tzBTC_shares'] = 4

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 1)

        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], ALICE_ADDRESS)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 3)  # value

        self.assertEqual(new_storage['tzBTC_shares'], 1)
        del initial_storage['tzBTC_shares']
        del new_storage['tzBTC_shares']
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
        initial_storage['tzBTC_shares'] = 1

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
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
        initial_storage['tzBTC_shares'] = 1

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(new_storage, initial_storage)

        # case positive but actual shares value zero
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['gross_credit_index'] = 2_000_000_000_000
        initial_storage['total_gross_credit'] = 2_000_000_000_000 - 1
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 2_000_000_000_000
        initial_storage['tzBTC_shares'] = 1

        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            storage = initial_storage,
            sender = ALICE_ADDRESS,
            now = 0,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(new_storage, initial_storage)

    def test_forbidden_case(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.withdrawCommission().run_code(storage=initial_storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

    def test_update_dttm(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        result = run_code_patched(
            self.lending_contract.withdrawCommission(),
            amount = 0,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        self.assertEqual(result.storage['index_update_dttm'], 0)
