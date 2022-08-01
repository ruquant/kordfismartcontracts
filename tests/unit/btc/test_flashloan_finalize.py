from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class FlashloanFinalizeEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['flashloan_shares'] = 0
        with self.assertNotRaises(Exception):
            self.lending_contract.flashloanFinalize().run_code(storage=initial_storage)

        initial_storage['flashloan_shares'] = 1
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.flashloanFinalize().run_code(storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'loan error')
