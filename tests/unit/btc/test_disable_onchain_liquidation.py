from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class SetDelegateEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = self.lending_contract.disableOnchainLiquidation().run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )

        self.assertEqual(len(result.operations), 0)
        self.assertFalse(result.storage['onchain_liquidation_available'])

        del result.storage['onchain_liquidation_available']
        del initial_storage['onchain_liquidation_available']
        self.assertDictEqual(result.storage, initial_storage)

        # already disabled
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['onchain_liquidation_available'] = False

        result = self.lending_contract.disableOnchainLiquidation().run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(result.storage, initial_storage)

    def test_forbidden_case(self):
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.disableOnchainLiquidation().run_code(storage=storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
