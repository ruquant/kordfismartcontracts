from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE


class RedeemLBFinalizeEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['lb_shares'] = 10

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 3_000_000_000_000

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 4_500_000_000_000,
                'gross_credit': 6_000_000_000_000,
            }
        }

        result = self.lending_contract.redeemLBFinalize(BOB_ADDRESS, 10, 10 ** 6).run_code(
            amount = 0,
            balance = 21 * 10 ** 6,
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['lb_shares'], 10)

        self.assertEqual(new_storage['total_net_credit'], 500_000_000_000)
        self.assertEqual(new_storage['net_credit_index'], 2_000_000_000_000)
        self.assertEqual(new_storage['total_gross_credit'], 1_000_000_000_000)
        self.assertEqual(new_storage['gross_credit_index'], 3_000_000_000_000)

        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['lb_shares'], 0)
        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['net_credit'], 0)
        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['gross_credit'], 0)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 2_000_000)
        self.assertEqual(operation['destination'], BOB_ADDRESS)

    def test_balance_delta_error(self):
        self_address = self.lending_contract.context.get_self_address()
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 4_000_000_000_000

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 2_000_000_000_000,
                'gross_credit': 2_500_000_000_000,
            }
        }
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.redeemLBFinalize(BOB_ADDRESS, 10, 2 * 10 ** 6).run_code(
                amount = 0,
                balance = 10 ** 6,
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'negative balance delta error')

    def test_forbidden(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.redeemLBFinalize(BOB_ADDRESS, 100, 100).run_code(storage=initial_storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        initial_storage = deepcopy(DEFAULT_STORAGE)
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.redeemLBFinalize(BOB_ADDRESS, 100, 100).run_code(storage=initial_storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

    def test_partial_redeem(self):
        self_address = self.lending_contract.context.get_self_address()
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['lb_shares'] = 10

        initial_storage['total_net_credit'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 2_000_000_000_000

        initial_storage['total_gross_credit'] = 7_000_000_000_000
        initial_storage['gross_credit_index'] = 3_000_000_000_000

        initial_storage['liquidity_book'] = {
            BOB_ADDRESS: {
                'lb_shares': 10,
                'net_credit': 4_500_000_000_000,
                'gross_credit': 6_000_000_000_000,
            }
        }

        result = self.lending_contract.redeemLBFinalize(BOB_ADDRESS, 7, 10 ** 6).run_code(
            amount = 0,
            balance = 21 * 10 ** 6,
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(new_storage['lb_shares'], 10)

        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['lb_shares'], 3)
        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['net_credit'], 1_350_000_000_000)
        self.assertEqual(new_storage['liquidity_book'][BOB_ADDRESS]['gross_credit'], 1_800_000_000_000)

        self.assertEqual(new_storage['total_net_credit'], 1_850_000_000_000)
        self.assertEqual(new_storage['net_credit_index'], 2_000_000_000_000)

        self.assertEqual(new_storage['total_gross_credit'], 2_800_000_000_000)
        self.assertEqual(new_storage['gross_credit_index'], 3_000_000_000_000)

        self.assertEqual(len(result.operations), 1)
        operation = result.operations[0]
        self.assertEqual(operation['kind'], 'transaction')
        self.assertEqual(int(operation['amount']), 7_400_000)
        self.assertEqual(operation['destination'], BOB_ADDRESS)
