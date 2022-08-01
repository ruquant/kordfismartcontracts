from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, INFINITY_NAT
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class InvestLBEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_no_upfront_commission_only_amount2Lqt(self):
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
        initial_storage['tzBTC_shares'] = 17
        initial_storage['upfront_commission'] = 0

        result = run_code_patched(
            # amount2tzBTC, mintzBTCTokensBought, tzBTC2xtz, minXtzBought, amount2Lqt, minLqtMinted
            self.lending_contract.investLB(0, 0, 0, 0, 40, 45),
            amount = 25,
            balance = 300,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 10)
        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertEqual(new_storage['lb_shares'], 9)
        self.assertEqual(new_storage['tzBTC_shares'], 17)

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

        # approve tzBTC
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), INFINITY_NAT)  # value

        # addLiquidity
        operation = result.operations[4]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 40)
        self.assertEqual(operation['destination'], liquidity_baking_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'addLiquidity')

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address) # owner
        self.assertEqual(int(params[1]['int']), 45) # minLqtMinted
        self.assertEqual(int(params[2]['int']), INFINITY_NAT) # maxTokensDeposited
        self.assertEqual(int(params[3]['int']), 108) # deadline

        # approve tzBTC
        operation = result.operations[5]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], liquidity_baking_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), 0)  # value

        # sellXtz
        operation = result.operations[6]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'sellXtz')

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

        # investLBFinalize
        operation = result.operations[9]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'investLBFinalize')

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # address
        self.assertEqual(int(params[1]['int']), 9)  # initial_lb_shares
        self.assertEqual(int(params[2]['int']), 17)  # initial_tzBTC_shares
        self.assertEqual(int(params[3]['int']), 0)  # tzBTC2xtz

    def test_upfront_commission(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = self.dex_contract.context.address
        initial_storage['dex_contract_address'] = self.another_dex_contract.context.address
        initial_storage['fa_tzBTC_address'] = self.tzbtc_token.context.address
        initial_storage['fa_lb_address'] = self.lqt_token.context.address

        # case 2%
        initial_storage['upfront_commission'] = 2_000  # 2%

        # amount2tzBTC, mintzBTCTokensBought, tzBTC2xtz, minXtzBought, amount2Lqt, minLqtMinted
        result = self.lending_contract.investLB(0, 0, 0, 0, 15_000, 0).run_code(
            amount = 10_000 + 400,
            balance = 0,
            storage = initial_storage,
            sender = BOB_ADDRESS,
        )

        # send upfrount commission to admin
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 400)
        self.assertEqual(operation['destination'], ALICE_ADDRESS)

        # case 1%
        initial_storage['upfront_commission'] = 1_000  # 1%

        # amount2tzBTC, mintzBTCTokensBought, tzBTC2xtz, minXtzBought, amount2Lqt, minLqtMinted
        result = self.lending_contract.investLB(0, 0, 0, 0, 15_000, 0).run_code(
            amount = 10_000 + 200,
            balance = 0,
            storage = initial_storage,
            sender = BOB_ADDRESS,
        )

        # send upfrount commission to admin
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 200)
        self.assertEqual(operation['destination'], ALICE_ADDRESS)

    def test_no_upfront_commission_with_amount2tzbtc(self):
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
        initial_storage['tzBTC_shares'] = 17
        initial_storage['upfront_commission'] = 0

        result = run_code_patched(
            # amount2tzBTC, mintzBTCTokensBought, tzBTC2xtz, minXtzBought, amount2Lqt, minLqtMinted
            self.lending_contract.investLB(20, 25, 30, 35, 40, 45),
            amount = 27,
            balance = 300,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 11)
        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertEqual(new_storage['lb_shares'], 9)
        self.assertEqual(new_storage['tzBTC_shares'], 17)

        self_address = self.lending_contract.context.get_self_address()

        # xtzToToken
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 20)
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
        self.assertEqual(int(operation['amount']), 40)
        self.assertEqual(operation['destination'], liquidity_baking_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'addLiquidity')

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address) # owner
        self.assertEqual(int(params[1]['int']), 45) # minLqtMinted
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

        # sellXtz
        operation = result.operations[7]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'sellXtz')

        # getBalance LB
        operation = result.operations[8]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_lb_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getBalance')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # owner
        # check contracts address at least
        self.assertAddressFromBytesEquals(params[1]['bytes'], self_address)  # callback

        # getBalance tzBTC
        operation = result.operations[9]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'getBalance')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # owner
        # check contracts address at least
        self.assertAddressFromBytesEquals(params[1]['bytes'], self_address)  # callback

        # investLBFinalize
        operation = result.operations[10]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'investLBFinalize')

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # address
        self.assertEqual(int(params[1]['int']), 9)  # initial_lb_shares
        self.assertEqual(int(params[2]['int']), 17)  # initial_tzBTC_shares
        self.assertEqual(int(params[3]['int']), 30)  # tzBTC2xtz

    def test_no_upfront_commission_with_tzbtc2xtz(self):
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
        initial_storage['tzBTC_shares'] = 17
        initial_storage['upfront_commission'] = 0

        result = run_code_patched(
            # amount2tzBTC, mintzBTCTokensBought, tzBTC2xtz, minXtzBought, amount2Lqt, minLqtMinted
            self.lending_contract.investLB(0, 25, 30, 35, 40, 45),
            amount = 27,
            balance = 300,
            storage = initial_storage,
            now = 107,
            sender = BOB_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 13)
        self.assertEqual(new_storage['index_update_dttm'], 0)
        self.assertEqual(new_storage['lb_shares'], 9)
        self.assertEqual(new_storage['tzBTC_shares'], 17)

        self_address = self.lending_contract.context.get_self_address()

        # approve tzBTC
        operation = result.operations[3]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], dex_contract_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), 30)  # value

        # tokenToXtz
        operation = result.operations[4]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], dex_contract_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'tokenToXtz') 

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # to
        self.assertEqual(int(params[1]['int']), 30)  # tokensSold
        self.assertEqual(int(params[2]['int']), 35)  # minXtzBought
        self.assertEqual(int(params[3]['int']), 108) # deadline

        # approve tzBTC
        operation = result.operations[5]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'approve')

        self.assertAddressFromBytesEquals(operation['parameters']['value']['args'][0]['bytes'], dex_contract_address)  # spender
        self.assertEqual(int(operation['parameters']['value']['args'][1]['int']), 0)  # value

        # investLBFinalize
        operation = result.operations[12]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], self_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'investLBFinalize')

        params = operation['parameters']['value']
        self.assertAddressFromBytesEquals(params[0]['bytes'], BOB_ADDRESS)  # address
        self.assertEqual(int(params[1]['int']), 9)  # initial_lb_shares
        self.assertEqual(int(params[2]['int']), 17)  # initial_tzBTC_shares
        self.assertEqual(int(params[3]['int']), 30)  # tzBTC2xtz

    def test_bad_sent_amount(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = self.dex_contract.context.address
        initial_storage['dex_contract_address'] = self.another_dex_contract.context.address
        initial_storage['fa_tzBTC_address'] = self.tzbtc_token.context.address
        initial_storage['fa_lb_address'] = self.lqt_token.context.address

        # with zero upfront commission
        initial_storage['upfront_commission'] = 0

        with self.assertNotRaises(Exception):
            self.lending_contract.investLB(3 * 10**6, 0, 0, 0, 7 * 10**6, 0).run_code(
                amount = 10 * 10**6,
                storage = initial_storage,
            )
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLB(3 * 10**6, 0, 0, 0, 7 * 10**6, 0).run_code(
                amount = 10 * 10**6 + 1,
                storage = initial_storage,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'sent amount error')

        # with non-zero upfront commission
        initial_storage['upfront_commission'] = 2_000

        with self.assertNotRaises(Exception):
            self.lending_contract.investLB(3 * 10**6, 0, 0, 0, 7 * 10**6, 0).run_code(
                amount = 10 * 10**6 + 8 * 10**4,
                storage = initial_storage,
                sender = BOB_ADDRESS,
            )
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLB(3 * 10**6, 0, 0, 0, 7 * 10**6, 0).run_code(
                amount = 10 * 10**6 + 8 * 10**4 + 1,
                storage = initial_storage,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'sent amount error')
