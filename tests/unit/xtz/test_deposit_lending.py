from copy import deepcopy


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE


class DepositLendingEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        selected_mutez_amount = 9_123_456

        # case normal - empty depost book
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 1_000_000_000_000
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        
        result = run_code_patched(
            self.lending_contract.depositLending(),
            amount = selected_mutez_amount,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
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

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertDictEqual(new_storage['ledger'], {
            BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}},
        })
        self.assertEqual(new_storage['totalSupply'], 5_561_728_000_000)
    
        # case - filled deposit book
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}
        initial_storage['totalSupply'] = 5_561_728_000_000
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address

        result = run_code_patched(
            self.lending_contract.depositLending(),
            amount = selected_mutez_amount,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)
        self.assertEqual(len(result.operations), 3)
        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertDictEqual(new_storage['ledger'], {BOB_ADDRESS: {'balance': 9_123_456_000_000, 'approvals': {}}})
        self.assertEqual(new_storage['totalSupply'], 10_123_456_000_000)

        # case - admin case
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 1_000_000_000_000
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        
        result = run_code_patched(
            self.lending_contract.depositLending(),
            amount = selected_mutez_amount,
            balance = 0,
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 3)
        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertDictEqual(new_storage['ledger'], {ALICE_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}})
        self.assertEqual(new_storage['totalSupply'], 5_561_728_000_000)
