from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE


class SetUpfrontCommissionEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        # case normal
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = self.lending_contract.setUpfrontCommission(1_500).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertEqual(new_storage['upfront_commission'], 1_500)

        del new_storage['upfront_commission']
        del initial_storage['upfront_commission']
        self.assertDictEqual(new_storage, initial_storage)

        # case max value
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = self.lending_contract.setUpfrontCommission(2_000).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertEqual(new_storage['upfront_commission'], 2_000)

        del new_storage['upfront_commission']
        del initial_storage['upfront_commission']
        self.assertDictEqual(new_storage, initial_storage)

    def test_forbidden(self):
        # forbidden case
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.setUpfrontCommission(0).run_code(sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # max value error case
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.setUpfrontCommission(2_001).run_code(sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'upfront commission max value error')
