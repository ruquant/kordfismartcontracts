from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, DEFAULT_STORAGE, INFINITY_NAT, CONST_RATE_PARAMS


class InvestLBFinalizeEntryUnitTest(LendingContractBaseTestCase):
    
    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()

        # case normal
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['totalSupply'] = 10_000_000_000_000
        initial_storage['total_net_credit'] = 0
        initial_storage['total_gross_credit'] = 0
        initial_storage['lb_shares'] = 300

        initial_storage['gross_credit_index'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 4_000_000_000_000
        initial_storage['deposit_index'] = 2_000_000_000_000

        result = self.lending_contract.investLBFinalize(
            address = BOB_ADDRESS,
            initial_balance = 4 * 10 ** 6,
            initial_lb_shares = 0,
        ).run_code(
            amount = 0,
            balance = 10 ** 6,
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['total_net_credit'], 750_000_000_000)
        self.assertEqual(new_storage['total_gross_credit'], 600_000_000_000)
        self.assertEqual(new_storage['lb_shares'], 300)

        self.assertDictEqual(new_storage['liquidity_book'], 
            {BOB_ADDRESS: {
                'net_credit': 750_000_000_000,
                'gross_credit': 600_000_000_000,
                'lb_shares': 300,
            }})

        # case non empty initial data
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['totalSupply'] = 10_000_000_000_000
        initial_storage['total_net_credit'] = 250_000_000_000
        initial_storage['total_gross_credit'] = 200_000_000_000
        initial_storage['lb_shares'] = 800

        initial_storage['gross_credit_index'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 4_000_000_000_000
        initial_storage['deposit_index'] = 2_000_000_000_000

        initial_storage['liquidity_book'] = {BOB_ADDRESS: {
                'net_credit': 250_000_000_000,
                'gross_credit': 200_000_000_000,
                'lb_shares': 100,
            }
        }

        result = self.lending_contract.investLBFinalize(
            address = BOB_ADDRESS,
            initial_balance = 2 * 10 ** 6,
            initial_lb_shares = 200,
        ).run_code(
            amount = 0,
            balance = 10 ** 6,
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['total_net_credit'], 500_000_000_000)
        self.assertEqual(new_storage['total_gross_credit'], 400_000_000_000)
        self.assertEqual(new_storage['lb_shares'], 800)

        self.assertDictEqual(new_storage['liquidity_book'], 
            {BOB_ADDRESS: {
                'net_credit': 500_000_000_000,
                'gross_credit': 400_000_000_000,
                'lb_shares': 700,
            }})

    def test_impossible_cases(self):
        self_address = self.lending_contract.context.get_self_address()

        # balance delta error
        initial_storage = deepcopy(DEFAULT_STORAGE)
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 5 * 10**5, 0).run_code(storage=initial_storage, balance=10**6, sender=self_address)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'negative balance delta error')

        # lb delta error
        initial_storage = deepcopy(DEFAULT_STORAGE)
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 2 * 10 ** 6, 200).run_code(storage=initial_storage, balance=10**6, sender=self_address)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'negative lb delta error')

    def test_forbidden_cases(self):
        # admin tries
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 0, 0).run_code(sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # not admin tries
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 0, 0).run_code(sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

    def test_totalSupply_net_credit_inequation(self):
        self_address = self.lending_contract.context.get_self_address()

        # ok case
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 1_500_000_000_000

        initial_storage['total_net_credit'] = 0
        initial_storage['net_credit_index'] = 4_000_000_000_000

        with self.assertNotRaises(Exception):
            self.lending_contract.investLBFinalize(
                address = BOB_ADDRESS,
                initial_balance = 4 * 10 ** 6,
                initial_lb_shares = 0,
            ).run_code(
                amount = 0,
                balance = 10 ** 6,
                storage = initial_storage,
                sender = self_address,
            )

        # fail case
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 1_500_000_000_000 - 1

        initial_storage['total_net_credit'] = 0
        initial_storage['net_credit_index'] = 4_000_000_000_000

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(
                address = BOB_ADDRESS,
                initial_balance = 4 * 10 ** 6,
                initial_lb_shares = 0,
            ).run_code(
                amount = 0,
                balance = 10 ** 6,
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'total deposit and net credit inequation error')
