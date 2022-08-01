from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, CONTRACT_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class SetFlashloanParamsEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        # case normal: 123, 456, True
        initial_storage = deepcopy(DEFAULT_STORAGE)
        result = self.lending_contract.setFlashloanParams(123, 456, True).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertTrue(new_storage['flashloan_available'])
        del initial_storage['flashloan_available']
        del new_storage['flashloan_available']

        self.assertEqual(new_storage['flashloan_admin_commission'], 123)
        del initial_storage['flashloan_admin_commission']
        del new_storage['flashloan_admin_commission']

        self.assertEqual(new_storage['flashloan_deposit_commission'], 456)
        del initial_storage['flashloan_deposit_commission']
        del new_storage['flashloan_deposit_commission']

        self.assertDictEqual(new_storage, initial_storage)

        # case 2: 40, 110, False
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['flashloan_available'] = False
        result = self.lending_contract.setFlashloanParams(111, 333, True).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertTrue(new_storage['flashloan_available'])
        del initial_storage['flashloan_available']
        del new_storage['flashloan_available']

        self.assertEqual(new_storage['flashloan_admin_commission'], 111)
        del initial_storage['flashloan_admin_commission']
        del new_storage['flashloan_admin_commission']

        self.assertEqual(new_storage['flashloan_deposit_commission'], 333)
        del initial_storage['flashloan_deposit_commission']
        del new_storage['flashloan_deposit_commission']

        self.assertDictEqual(new_storage, initial_storage)

    def test_forbidden_case(self):
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setFlashloanParams(123, 456, True).run_code(storage=storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
