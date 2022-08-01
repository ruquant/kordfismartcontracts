from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, CONTRACT_ADDRESS, CLARE_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class UpdateTzBTCCallbackEntryUnitTest(LendingContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['administrator'] = ALICE_ADDRESS
        initial_storage['fa_tzBTC_address'] = CONTRACT_ADDRESS
        initial_storage['tzBTC_shares'] = 100
        initial_storage['local_params']['fa_tzBTC_callback_status'] = True

        result = self.lending_contract.updateTzBTCCallback(200).run_code(sender=CONTRACT_ADDRESS, storage=initial_storage)
        
        self.assertEqual(len(result.operations), 0)
        
        new_storage = deepcopy(result.storage)
        self.assertFalse(new_storage['local_params']['fa_tzBTC_callback_status'])
        self.assertEqual(new_storage['tzBTC_shares'], 200)

        del initial_storage['tzBTC_shares']
        del new_storage['tzBTC_shares']
        del initial_storage['local_params']['fa_tzBTC_callback_status']
        del new_storage['local_params']['fa_tzBTC_callback_status']
        self.assertDictEqual(new_storage, initial_storage)

    def test_fail_cases(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['administrator'] = ALICE_ADDRESS
        initial_storage['fa_tzBTC_address'] = CONTRACT_ADDRESS

        # true flag status - wrong senders
        initial_storage['local_params']['fa_tzBTC_callback_status'] = True
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.updateTzBTCCallback(200).run_code(sender=ALICE_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.updateTzBTCCallback(200).run_code(sender=CLARE_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # false flag status - different senders
        initial_storage['local_params']['fa_tzBTC_callback_status'] = False

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.updateTzBTCCallback(200).run_code(sender=ALICE_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.updateTzBTCCallback(200).run_code(sender=CONTRACT_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Bad status.')

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.updateTzBTCCallback(200).run_code(sender=CLARE_ADDRESS, storage=initial_storage)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
