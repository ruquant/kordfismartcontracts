from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, CONTRACT_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class SellXtzEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        dex_contract_address = self.another_dex_contract.context.address

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['dex_contract_address'] = dex_contract_address

        # zero balance case
        result = self.lending_contract.sellXtz().run_code(
            balance = 0,
            storage = initial_storage,
            sender = self_address,
        )

        self.assertEqual(len(result.operations), 0)
        self.assertDictEqual(result.storage, initial_storage)

        # non zero balance case
        result = run_code_patched(
            self.lending_contract.sellXtz(),
            balance = 17,
            storage = initial_storage,
            sender = self_address,
            now = 107,
        )

        self.assertEqual(len(result.operations), 1)
        self.assertDictEqual(result.storage, initial_storage)

        # xtzToToken
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 17)
        self.assertEqual(operation['destination'], dex_contract_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'xtzToToken')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['args'][0]['int']), 0)  # minTokensBought
        self.assertEqual(int(params[1]['args'][1]['int']), 108)  # deadline

    def test_fail_cases(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['administrator'] = ALICE_ADDRESS
        initial_storage['fa_tzBTC_address'] = CONTRACT_ADDRESS

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.sellXtz().run_code(sender=ALICE_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.sellXtz().run_code(sender=BOB_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
