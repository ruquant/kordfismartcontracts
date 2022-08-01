from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE, INFINITY_NAT


class SellTzBTCEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        liquidity_baking_address = self.dex_contract.context.address
        dex_contract_address = self.another_dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['dex_contract_address'] = dex_contract_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['local_params']['fa_tzBTC_callback_status'] = True

        result = run_code_patched(
            self.lending_contract.sellTzBTC(300),
            amount = 0,
            balance = 0,
            storage = initial_storage,
            sender = fa_tzBTC_address,
            now = 107,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 3)
        self.assertFalse(new_storage['local_params']['fa_tzBTC_callback_status'])

        self_address = self.lending_contract.context.get_self_address()

        # approve tzBTC
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], dex_contract_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), INFINITY_NAT)  # value

        # tokenToXtz
        operation = result.operations[1]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], dex_contract_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'tokenToXtz') 

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['int']), 300)  # tokensSold
        self.assertEqual(int(params[2]['int']), 0)  # minXtzBought
        self.assertEqual(int(params[3]['int']), 108) # deadline

        # approve tzBTC
        operation = result.operations[2]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve') 

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], dex_contract_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), 0)  # value

    def test_forbidden(self):
        liquidity_baking_address = self.dex_contract.context.address
        dex_contract_address = self.another_dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['dex_contract_address'] = dex_contract_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['local_params']['fa_tzBTC_callback_status'] = True

        # admin tries flag true
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.sellTzBTC(100).run_code(storage=initial_storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # not admin tries flag true
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.sellTzBTC(100).run_code(storage=initial_storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # bad callback status
        initial_storage['local_params']['fa_tzBTC_callback_status'] = False

        # admin tries flag false
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.sellTzBTC(100).run_code(storage=initial_storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # not admin tries flag false
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.sellTzBTC(100).run_code(storage=initial_storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # right contract tries but flag false
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.sellTzBTC(100).run_code(storage=initial_storage, sender=fa_tzBTC_address)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Bad status.')
