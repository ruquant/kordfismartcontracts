from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import DEFAULT_STORAGE, ALICE_ADDRESS, BOB_ADDRESS


class RedeemLendingEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address

        # case - normal
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}
        initial_storage['totalSupply'] = 5_561_728_000_000

        result = run_code_patched(
            self.lending_contract.redeemLending(9_000_000),
            amount = 0,
            balance = 10_000_000,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 4)

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

        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 9_000_000)
        self.assertEqual(operation['destination'], BOB_ADDRESS)

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertDictEqual(new_storage['ledger'], {BOB_ADDRESS: {'balance': 61_728_000_000, 'approvals': {}}})
        self.assertEqual(new_storage['totalSupply'], 1_061_728_000_000)

        # case - max amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['deposit_index'] = 4_000_000_000_000
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}
        initial_storage['totalSupply'] = 5_561_728_000_000
        result = run_code_patched(
            self.lending_contract.redeemLending(18_246_912),
            amount = 0,
            balance = 20_000_000,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 4)
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 18_246_912)
        self.assertEqual(operation['destination'], BOB_ADDRESS)

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertDictEqual(new_storage['ledger'], {BOB_ADDRESS: {'balance': 0, 'approvals': {}}})
        self.assertEqual(new_storage['totalSupply'], 1_000_000_000_000)

        # case - too much amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['deposit_index'] = 4_000_000_000_000
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}
        with self.assertRaises(MichelsonError) as context:
            result = self.lending_contract.redeemLending(18_246_913).run_code(
                storage = initial_storage,
                sender = BOB_ADDRESS,
                balance = 20_000_000,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'too much amount')

        # case - not enough balance
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_000_000_000_000, 'approvals': {}}}
        with self.assertRaises(MichelsonError) as context:
            result = self.lending_contract.redeemLending(1_000_000).run_code(
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Not enough balance')

        # case - missing storage info
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        with self.assertRaises(MichelsonError) as context:
            result = self.lending_contract.redeemLending(18_246_913).run_code(
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        self.assertEqual(context.exception.args[0]['with']['string'], 'Unknown Address.')

        # case - admin
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['ledger'] = {ALICE_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}
        initial_storage['totalSupply'] = 5_561_728_000_000

        result = run_code_patched(
            self.lending_contract.redeemLending(9_000_000),
            amount = 0,
            balance = 10_000_000,
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 4)
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 9_000_000)
        self.assertEqual(operation['destination'], ALICE_ADDRESS)

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertDictEqual(new_storage['ledger'], {ALICE_ADDRESS: {'balance': 61_728_000_000, 'approvals': {}}})
        self.assertEqual(new_storage['totalSupply'], 1_061_728_000_000)

        # case - wrong total deposit value
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}

        with self.assertRaises(MichelsonError) as context:
            result = run_code_patched(
                self.lending_contract.redeemLending(9_000_000),
                amount = 0,
                balance = 10_000_000,
                storage = initial_storage,
                now = 107,
                sender = BOB_ADDRESS,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'wrong total deposit value')

    def test_totalSupply_net_credit_inequation(self):
        self_address = self.lending_contract.context.get_self_address()
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address

        # ok case
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}
        initial_storage['totalSupply'] = 5_000_000_000_000
        initial_storage['total_net_credit'] = 3_000_000_000_000
        initial_storage['net_credit_index'] = 2_500_000_000_000

        with self.assertNotRaises(Exception):
            self.lending_contract.redeemLending(2_500_000).run_code(
                balance = 10_000_000,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )

        # fail case
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['ledger'] = {BOB_ADDRESS: {'balance': 4_561_728_000_000, 'approvals': {}}}
        initial_storage['totalSupply'] = 5_000_000_000_000
        initial_storage['total_net_credit'] = 3_000_000_000_000
        initial_storage['net_credit_index'] = 2_500_000_000_000

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.redeemLending(2_500_001).run_code(
                balance = 10_000_000,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'total deposit and net credit inequation error')
