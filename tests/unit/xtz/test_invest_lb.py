from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE, INFINITY_NAT


class InvestLBEntryUnitTest(LendingContractBaseTestCase):

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
        initial_storage['lb_shares'] = 9

        result = run_code_patched(
            # amount2tzBTC, mintzBTCTokensBought, amount2Lqt, minLqtMinted, tzBTCShares
            self.lending_contract.investLB(10, 25, 30, 40, 0),
            amount = 15,
            balance = 300,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 10)
        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertEqual(new_storage['lb_shares'], 9)

        self_address = self.lending_contract.context.get_self_address()

        # xtzToToken
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 10)
        self.assertEqual(operation['destination'], dex_contract_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'xtzToToken')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['args'][0]['int']), 25)  # minTokensBought
        self.assertEqual(int(params[1]['args'][1]['int']), 108)  # deadline

        # approve tzBTC
        operation = result.operations[4]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), INFINITY_NAT)  # value
        
        # addLiquidity
        operation = result.operations[5]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 30)
        self.assertEqual(operation['destination'], liquidity_baking_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'addLiquidity')

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address) # owner
        self.assertEqual(int(params[1]['int']), 40) # minLqtMinted
        self.assertEqual(int(params[2]['int']), INFINITY_NAT) # maxTokensDeposited
        self.assertEqual(int(params[3]['int']), 108) # deadline

        # approve tzBTC
        operation = result.operations[6]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), 0)  # value

        # getBalance LB
        operation = result.operations[7]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_lb_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getBalance')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # owner
        # check contracts address at least
        self.assertAddressFromBytesEquals(params[1]['bytes'], self_address)  # callback

        # getBalance tzBTC
        operation = result.operations[8]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getBalance')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # owner
        # check contracts address at least
        self.assertAddressFromBytesEquals(params[1]['bytes'], self_address)  # callback

        # investLBFinalize - self_call
        operation = result.operations[9]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'investLBFinalize')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # address
        self.assertEqual(int(params[1]['args'][0]['int']), 285)  # initial_balance
        self.assertEqual(int(params[1]['args'][1]['int']), 9)  # initial_lb_shares

    def test_nonzero_upfront_commission_and_tz_btc_shares(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)
        liquidity_baking_address = self.dex_contract.context.address
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        dex_contract_address = self.another_dex_contract.context.address
        initial_storage['dex_contract_address'] = dex_contract_address
        fa_tzBTC_address = self.tzbtc_token.context.address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        fa_lb_address = self.lqt_token.context.address
        initial_storage['fa_lb_address'] = fa_lb_address

        result = self.lending_contract.investLB(10 * 10**6, 0, 30 * 10**6, 0, 222).run_code(
            amount = 10 * 10**6 + 3 * 10**5,
            balance = 10**10,
            storage = initial_storage,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 12)

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

        # send upfrount commission
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 3 * 10**5)
        self.assertEqual(operation['destination'], ALICE_ADDRESS)

        # transfer tzBTC
        operation = result.operations[4]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 222)  # value

    def test_leverage(self):
        liquidity_baking_address = self.dex_contract.context.address
        fa_tzBTC_address = self.tzbtc_token.context.address
        fa_lb_address = self.lqt_token.context.address
        dex_contract_address = self.another_dex_contract.context.address

        # with zero upfront commission
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['dex_contract_address'] = dex_contract_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address

        initial_storage['upfront_commission'] = 0

        # leverage = 4
        with self.assertNotRaises(Exception):
            self.lending_contract.investLB(10 * 10**6, 0, 30 * 10**6, 0, 0).run_code(
                amount = 10 * 10**6,
                balance = 10**10,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        # leverage > 4
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLB(10 * 10**6 + 1, 0, 30 * 10**6, 0, 0).run_code(
                amount = 10 * 10**6,
                balance = 10**10,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')

        # changing max leverage with storage to 5
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['dex_contract_address'] = dex_contract_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address

        initial_storage['upfront_commission'] = 0
        initial_storage['max_leverage'] = 50

        # leverage = 5
        with self.assertNotRaises(Exception):
            self.lending_contract.investLB(20 * 10**6, 0, 30 * 10**6, 0, 0).run_code(
                amount = 10 * 10**6,
                balance = 10**10,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        # leverage > 5
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLB(20 * 10**6 + 1, 0, 30 * 10**6, 0, 0).run_code(
                amount = 10 * 10**6,
                balance = 10**10,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')

        # with non-zero upfront commission
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = liquidity_baking_address
        initial_storage['dex_contract_address'] = dex_contract_address
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address
        initial_storage['fa_lb_address'] = fa_lb_address

        initial_storage['upfront_commission'] = 2000

        # leverage = 4
        with self.assertNotRaises(Exception):
            self.lending_contract.investLB(10 * 10**6, 0, 30 * 10**6, 0, 0).run_code(
                amount = 10 * 10**6 + 6 * 10**5,
                balance = 10**10,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        # leverage > 4
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLB(10 * 10**6 + 1, 0, 30 * 10**6, 0, 0).run_code(
                amount = 10 * 10**6 + 6 * 10**5,
                balance = 10**10,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')
