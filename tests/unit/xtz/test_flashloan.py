from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, CONTRACT_ADDRESS, DEFAULT_STORAGE


class FlashloanEntryUnitTest(LendingContractBaseTestCase):

    def test_basic_transactions(self):
        self_address = self.lending_contract.context.get_self_address()

        callback_entrypoint_name = 'default'
        callback_contract_address = self.oracle.context.address
        callback_entrypoint_adress = f'{callback_contract_address}%{callback_entrypoint_name}'

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['administrator'] = ALICE_ADDRESS
        initial_storage['flashloan_available'] = True
        initial_storage['index_update_dttm'] = 107

        result = run_code_patched(
            self.lending_contract.flashloan(callback_entrypoint_adress, 111),
            sender=BOB_ADDRESS,
            storage=initial_storage, 
            balance=222,
            now = 107,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 2)

        # callback
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 111)
        self.assertEqual(operation['destination'], callback_contract_address)
        # self.assertEqual(operation['parameters']['entrypoint'], callback_entrypoint_name)
        # seems like this doesn't work with default entry

        # flashloanFinalize - self_call
        operation = result.operations[1]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'flashloanFinalize')

    def test_forbidden_cases(self):
        entrypoint_adress = f'{self.oracle.context.address}%default'

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['administrator'] = ALICE_ADDRESS
        initial_storage['flashloan_available'] = False

        # admin tries
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.flashloan(entrypoint_adress, 100).run_code(sender=ALICE_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'flashloan is not available')

        # non admin tries
        with self.assertRaises(MichelsonError) as context:
           self.lending_contract.flashloan(entrypoint_adress, 100).run_code(sender=BOB_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'flashloan is not available')

        # with zero amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['flashloan_available'] = True
        with self.assertRaises(MichelsonError) as context:
           self.lending_contract.flashloan(entrypoint_adress, 0).run_code(sender=BOB_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'zero requested amount')

    def test_rounding(self):
        callback_entrypoint_name = 'default'
        callback_contract_address = self.oracle.context.address
        callback_entrypoint_adress = f'{callback_contract_address}%{callback_entrypoint_name}'

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['flashloan_admin_commission'] = 123
        initial_storage['flashloan_deposit_commission'] = 456
        initial_storage['flashloan_available'] = True
        initial_storage['index_update_dttm'] = 107

        result = run_code_patched(
            self.lending_contract.flashloan(callback_entrypoint_adress, 51_234_567),
            storage = initial_storage,
            now = 107,
        )
        self.assertEqual(result.storage['flashloan_amount'], 296_649 + 51_234_567)

    def test_non_zero_totalSupply(self):
        callback_entrypoint_name = 'default'
        callback_contract_address = self.oracle.context.address
        callback_entrypoint_adress = f'{callback_contract_address}%{callback_entrypoint_name}'

        # non zero total deposit case
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['flashloan_available'] = True
        initial_storage['totalSupply'] = 1_000_000_000_000
        initial_storage['index_update_dttm'] = 107

        result = run_code_patched(
            self.lending_contract.flashloan(callback_entrypoint_adress, 50),
            storage = initial_storage,
            now = 107,
        )
        new_storage = deepcopy(result.storage)
        self.assertEqual(new_storage['deposit_index'], 1_000_000_025_000)
