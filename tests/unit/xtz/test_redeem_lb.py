from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE, INFINITY_NAT


class RedeemLBEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address
        initial_storage['lb_shares'] = 400
        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'net_credit': 100,
                'gross_credit': 200,
                'lb_shares': 300,
            }
        }

        result = run_code_patched(
            self.lending_contract.redeemLB(250, 777),
            amount = 0,
            balance = 500,
            storage = initial_storage,
            sender = BOB_ADDRESS,
            now = 107,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertEqual(new_storage['lb_shares'], 150)
        self.assertEqual(len(result.operations), 8)

        self_address = self.lending_contract.context.get_self_address()
        # update lqt total
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_lb_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getTotalSupply')
        self.assertEqual(operation['parameters']['value']['args'][0]['prim'], 'Unit')
        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][1]['bytes'], self_address)

        # update tcbtc pool
        operation = result.operations[1]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getBalance')
        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)
        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][1]['bytes'], self_address)

        # calculate lb price
        operation = result.operations[2]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'calculateLbPrice')
        self.assertEqual(operation['parameters']['value']['prim'], 'Unit')

        # approve LB
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_lb_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), 250)  # value

        # removeLiquidity
        operation = result.operations[4]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], liquidity_baking_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'removeLiquidity') 

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['int']), 250)  # lqtBurned
        self.assertEqual(int(params[2]['int']), 0)  # minXtzWithdrawn
        self.assertEqual(int(params[3]['int']), 777)  # minTokensWithdrawn
        self.assertEqual(int(params[4]['int']), 108)  # deadline

        # approve LB
        operation = result.operations[5]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_lb_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), 0)  # value

        # getBalance - sellTzBTC
        operation = result.operations[6]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getBalance')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # owner
        # check contracts address at least
        self.assertAddressFromBytesEquals(params[1]['bytes'], self_address)  # callback

        # redeemLBFinalize - self_call
        operation = result.operations[7]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'redeemLBFinalize')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # address
        self.assertEqual(int(params[1]['args'][0]['int']), 250)  # lqtBurned
        self.assertEqual(int(params[1]['args'][1]['int']), 500)  # initial_balance

    def test_fail_cases(self):
        # amount is not allowed fail
        initial_storage = deepcopy(DEFAULT_STORAGE)
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.redeemLB(100, 100).run_code(storage=initial_storage, sender=BOB_ADDRESS, amount=100)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Amount is not allowed.')
