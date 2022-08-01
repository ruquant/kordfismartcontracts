from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE


class setIsWorkingStatusEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address

        # flag false
        initial_storage['is_working'] = False

        result = run_code_patched(
            self.lending_contract.setIsWorkingStatus(True),
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertTrue(new_storage['is_working'])
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

        # flag true
        initial_storage['is_working'] = True

        result = run_code_patched(
            self.lending_contract.setIsWorkingStatus(False),
            storage = initial_storage,
            now = 107,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertFalse(new_storage['is_working'])
        self.assertEqual(len(result.operations), 3)

    def test_forbidden_case(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        # flag false
        initial_storage['is_working'] = False
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.setIsWorkingStatus(True).run_code(sender=BOB_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # flag true
        initial_storage['is_working'] = True
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.setIsWorkingStatus(False).run_code(sender=BOB_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
