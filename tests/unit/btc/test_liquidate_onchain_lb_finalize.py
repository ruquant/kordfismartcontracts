from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, CLARE_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class LiquidateOnchainLBFinalizeEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        fa_tzBTC_address = self.tzbtc_token.context.address

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address

        initial_storage['totalSupply'] = 1_370_000_000_000_000
        initial_storage['deposit_index'] = 1_000_000_000_000

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 300_000_000_000_000

        initial_storage['lb_shares'] = 100
        initial_storage['tzBTC_shares'] = 2_000

        initial_storage['local_params']['fa_tzBTC_callback_status'] = False

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 4_500_000_000_000,
                'gross_credit': 6_000_000_000_000,
            }
        }

        result = self.lending_contract.liquidateOnchainLBFinalize(
            address = BOB_ADDRESS,
            initial_tzBTC_shares = 100,
        ).run_code(
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['total_net_credit'], 500_000_000_000)
        self.assertEqual(new_storage['net_credit_index'], 2_000_000_000_000)
        self.assertEqual(new_storage['total_gross_credit'], 1_000_000_000_000)
        self.assertEqual(new_storage['gross_credit_index'], 300_000_000_000_000)
        self.assertEqual(new_storage['lb_shares'], 100)

        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['lb_shares'], 0)
        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['net_credit'], 0)
        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['gross_credit'], 0)

        self.assertFalse(initial_storage['local_params']['fa_tzBTC_callback_status'])

        self.assertEqual(len(result.operations), 1)
        # transfer tzBTC
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], ALICE_ADDRESS)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 50)  # value

        self.assertEqual(new_storage['deposit_index'], 1_036_496_350_364)
        self.assertEqual(new_storage['totalSupply'], 1_370_000_000_000_000)

    def test_different_admin_liquidation_comm(self):
        self_address = self.lending_contract.context.get_self_address()
        fa_tzBTC_address = self.tzbtc_token.context.address

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address

        initial_storage['totalSupply'] = 1_370_000_000_000_000
        initial_storage['deposit_index'] = 1_000_000_000_000

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 300_000_000_000_000

        initial_storage['lb_shares'] = 100
        initial_storage['tzBTC_shares'] = 2_000

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 4_500_000_000_000,
                'gross_credit': 6_000_000_000_000,
            }
        }

        # admin_liquidation_comm 30 %
        initial_storage['onchain_liquidation_comm'] = 30

        result = self.lending_contract.liquidateOnchainLBFinalize(
            address = BOB_ADDRESS,
            initial_tzBTC_shares = 100,
        ).run_code(
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['deposit_index'], 1_051_094_890_510)
        self.assertEqual(new_storage['totalSupply'], 1_370_000_000_000_000)

        self.assertEqual(len(result.operations), 1)
        # transfer tzBTC
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], ALICE_ADDRESS)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 30)  # value

        # admin_liquidation_comm 70 %
        initial_storage['onchain_liquidation_comm'] = 70

        result = self.lending_contract.liquidateOnchainLBFinalize(
            address = BOB_ADDRESS,
            initial_tzBTC_shares = 100,
        ).run_code(
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['deposit_index'], 1_021_897_810_218)
        self.assertEqual(new_storage['totalSupply'], 1_370_000_000_000_000)

        self.assertEqual(len(result.operations), 1)
        # transfer tzBTC
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 0)
        self.assertEqual(operation['destination'], fa_tzBTC_address)
        self.assertEqual(operation['parameters']['entrypoint'], 'transfer')

        params = operation['parameters']['value']['args']
        self.assertAddressFromBytesEquals(params[0]['bytes'], self_address)  # from
        self.assertAddressFromBytesEquals(params[1]['args'][0]['bytes'], ALICE_ADDRESS)  # to
        self.assertEqual(int(params[1]['args'][1]['int']), 70)  # value

    def test_negative_extra(self):
        self_address = self.lending_contract.context.get_self_address()
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['totalSupply'] = 13_700_000_000_000
        initial_storage['deposit_index'] = 1_000_000_000_000

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 3_000_000_000_000

        initial_storage['lb_shares'] = 100
        initial_storage['tzBTC_shares'] = 17

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 4_500_000_000_000,
                'gross_credit': 6_000_000_000_000,
            }
        }

        result = self.lending_contract.liquidateOnchainLBFinalize(
            address = BOB_ADDRESS,
            initial_tzBTC_shares = 1,
        ).run_code(
            balance = 17,
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['deposit_index'], 854_014_598_540)
        self.assertEqual(new_storage['totalSupply'], 13_700_000_000_000)

        self.assertEqual(len(result.operations), 0)

    def test_liquidation_is_not_allowed(self):
        self_address = self.lending_contract.context.get_self_address()
        fa_tzBTC_address = self.tzbtc_token.context.address

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['fa_tzBTC_address'] = fa_tzBTC_address

        initial_storage['totalSupply'] = 13_700_000_000_000
        initial_storage['deposit_index'] = 1_000_000_000_000

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 400_000_000_000_000

        initial_storage['lb_shares'] = 100

        initial_storage['local_params']['fa_tzBTC_callback_status'] = False

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 2_000_000_000_000,
                'gross_credit': 2_500_000_000_000,
            }
        }

        # 120 %
        initial_storage['onchain_liquidation_percent'] = 120
        initial_storage['tzBTC_shares'] = 1_299
        # with self.assertNotRaises(Exception):
        self.lending_contract.liquidateOnchainLBFinalize(
            address = BOB_ADDRESS,
            initial_tzBTC_shares = 100,
        ).run_code(
            storage = initial_storage,
            sender = self_address,
        )

        initial_storage['tzBTC_shares'] = 1_300
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.liquidateOnchainLBFinalize(
                address = BOB_ADDRESS,
                initial_tzBTC_shares = 100,
            ).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'liquidation is not allowed')

        # 140 %
        initial_storage['onchain_liquidation_percent'] = 140
        initial_storage['tzBTC_shares'] = 1_499
        with self.assertNotRaises(Exception):
            self.lending_contract.liquidateOnchainLBFinalize(
                address = BOB_ADDRESS,
                initial_tzBTC_shares = 100,
            ).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        initial_storage['tzBTC_shares'] = 1_500
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.liquidateOnchainLBFinalize(
                address = BOB_ADDRESS,
                initial_tzBTC_shares = 100,
            ).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'liquidation is not allowed')

    def test_balance_delta_error(self):
        self_address = self.lending_contract.context.get_self_address()
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 4_000_000_000_000

        initial_storage['lb_shares'] = 10
        initial_storage['tzBTC_shares'] = 1

        initial_storage['local_params']['fa_tzBTC_callback_status'] = False

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 2_000_000_000_000,
                'gross_credit': 2_500_000_000_000,
            }
        }
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.liquidateOnchainLBFinalize(
                address = BOB_ADDRESS,
                initial_tzBTC_shares = 2,
            ).run_code(
                amount = 0,
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'negative tzBTC shares delta error')

    def test_forbidden(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.liquidateOnchainLBFinalize(BOB_ADDRESS, 0).run_code(storage=initial_storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        initial_storage = deepcopy(DEFAULT_STORAGE)
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.liquidateOnchainLBFinalize(BOB_ADDRESS, 0).run_code(storage=initial_storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
