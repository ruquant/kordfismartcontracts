from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, CLARE_ADDRESS, DEFAULT_STORAGE


class SetDelegateEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = self.lending_contract.setDelegate(BOB_ADDRESS).run_code(
            amount = 10 ** 6,
            balance = 0,
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )

        self.assertDictEqual(result.storage, initial_storage)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'delegation')
        self.assertEqual(operation['delegate'], BOB_ADDRESS)

    def test_forbidden_case(self):
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setDelegate(CLARE_ADDRESS).run_code(storage=storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
