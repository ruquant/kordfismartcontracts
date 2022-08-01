from copy import deepcopy


from ..base import LendingContractBaseTestCase
from ..constants import BOB_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class FlashloanReturnEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        fa_tzBTC_address = self.tzbtc_token.context.address

        # case less than flashloan amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['flashloan_shares'] = 100

        result = self.lending_contract.flashloanReturn(77).run_code(storage=initial_storage, sender=BOB_ADDRESS)

        self.assertEqual(result.storage['flashloan_shares'], 23)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 77)  # value

        # case more than flashloan amount
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['flashloan_shares'] = 100

        result = self.lending_contract.flashloanReturn(123).run_code(storage=initial_storage, sender=BOB_ADDRESS)

        self.assertEqual(result.storage['flashloan_shares'], 0)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 123)  # value
