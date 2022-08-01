from copy import deepcopy


from ..base import LendingContractBaseTestCase
from ..constants import DEFAULT_STORAGE


class FlashloanReturnEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        # case less than flashloan amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['flashloan_amount'] = 100

        result = self.lending_contract.flashloanReturn().run_code(amount=77, storage=initial_storage)

        self.assertEqual(len(result.operations), 0)
        self.assertEqual(result.storage['flashloan_amount'], 23)

        # case more than flashloan amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['flashloan_amount'] = 100

        result = self.lending_contract.flashloanReturn().run_code(amount=123, storage=initial_storage)

        self.assertEqual(len(result.operations), 0)
        self.assertEqual(result.storage['flashloan_amount'], 0)
