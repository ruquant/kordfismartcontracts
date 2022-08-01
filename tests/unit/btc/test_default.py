from copy import deepcopy


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import BOB_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class DefaultEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = run_code_patched(
            self.lending_contract.default(),
            amount = 10 ** 6,
            balance = 0,
            storage = initial_storage,
            now = 1,
            sender = BOB_ADDRESS,
        )

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(result.storage, initial_storage)
