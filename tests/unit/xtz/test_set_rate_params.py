from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE


class SetRateParamsEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        # case normal: 10 20 30 40
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        result = run_code_patched(
            self.lending_contract.setRateParams(10, 20, 30, 40),
            amount = 0,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

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

        self.assertEqual(new_storage['rate_params']['rate_1'], 10)
        self.assertEqual(new_storage['rate_params']['rate_diff'], 20)
        self.assertEqual(new_storage['rate_params']['threshold_percent_1'], 30)
        self.assertEqual(new_storage['rate_params']['threshold_percent_2'], 40)
        del initial_storage['rate_params']
        del new_storage['rate_params']

        self.assertEqual(new_storage['index_update_dttm'],0)
        del initial_storage['index_update_dttm']
        del new_storage['index_update_dttm']
  
        self.assertDictEqual(new_storage, initial_storage)

        # case 2: 50 60 70 80
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        result = run_code_patched(
            self.lending_contract.setRateParams(50, 60, 70, 80),
            amount = 0,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 3)

        self.assertEqual(new_storage['rate_params']['rate_1'], 50)
        self.assertEqual(new_storage['rate_params']['rate_diff'], 60)
        self.assertEqual(new_storage['rate_params']['threshold_percent_1'], 70)
        self.assertEqual(new_storage['rate_params']['threshold_percent_2'], 80)
        del initial_storage['rate_params']
        del new_storage['rate_params']

        self.assertEqual(new_storage['index_update_dttm'], 0)
        del initial_storage['index_update_dttm']
        del new_storage['index_update_dttm']
  
        self.assertDictEqual(new_storage, initial_storage)

        # max available values 12857 0 100 100
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        result = run_code_patched(
            self.lending_contract.setRateParams(12857, 0, 100, 100),
            amount = 0,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 3)

        self.assertEqual(new_storage['rate_params']['rate_1'], 12857)
        self.assertEqual(new_storage['rate_params']['rate_diff'], 0)
        self.assertEqual(new_storage['rate_params']['threshold_percent_1'], 100)
        self.assertEqual(new_storage['rate_params']['threshold_percent_2'], 100)
        del initial_storage['rate_params']
        del new_storage['rate_params']

        self.assertEqual(new_storage['index_update_dttm'], 0)
        del initial_storage['index_update_dttm']
        del new_storage['index_update_dttm']
  
        self.assertDictEqual(new_storage, initial_storage)

    def test_bad_params(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            storage['liquidity_baking_address'] = liquidity_baking_address
            storage['fa_tzBTC_address'] = fa_tzBTC_address
            storage['fa_lb_address'] = fa_lb_address
            self.lending_contract.setRateParams(12857, 1, 10, 20).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'rate2 max value error')

        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            storage['liquidity_baking_address'] = liquidity_baking_address
            storage['fa_tzBTC_address'] = fa_tzBTC_address
            storage['fa_lb_address'] = fa_lb_address
            self.lending_contract.setRateParams(10, 20, 10, 101).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'wrong threshold percent')

        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            storage['liquidity_baking_address'] = liquidity_baking_address
            storage['fa_tzBTC_address'] = fa_tzBTC_address
            storage['fa_lb_address'] = fa_lb_address
            self.lending_contract.setRateParams(10, 20, 30, 20).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'wrong threshold percent')

    def test_forbidden_case(self):
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setRateParams(10, 10, 10, 10).run_code(storage=storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
