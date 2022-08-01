from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class SetLbPriceChangeRateEntryUnitTest(LendingContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        # case normal
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = self.lending_contract.setLbPriceChangeRate(1_000).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertEqual(new_storage['lb_price_change_rate'], 1_000)

        del new_storage['lb_price_change_rate']
        del initial_storage['lb_price_change_rate']
        self.assertDictEqual(new_storage, initial_storage)

        # case max value
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = self.lending_contract.setLbPriceChangeRate(277_777_777).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)
        self.assertEqual(new_storage['lb_price_change_rate'], 277_777_777)

        del new_storage['lb_price_change_rate']
        del initial_storage['lb_price_change_rate']
        self.assertDictEqual(new_storage, initial_storage)

    def test_forbidden(self):
        # forbidden case
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.setLbPriceChangeRate(0).run_code(sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # max value error case
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.setLbPriceChangeRate(277_777_778).run_code(sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'price change rate max value error')
