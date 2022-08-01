from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase, run_code_patched
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, INFINITY_NAT
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class InvestLBFinalizeEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        self_address = self.lending_contract.context.get_self_address()

        # case normal
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['totalSupply'] = 100_000_000_000_000
        initial_storage['total_net_credit'] = 0
        initial_storage['total_gross_credit'] = 0

        initial_storage['lb_shares'] = 300
        initial_storage['tzBTC_shares'] = 2

        initial_storage['gross_credit_index'] = 5_000_000_000_000
        initial_storage['net_credit_index'] = 4_000_000_000_000
        initial_storage['deposit_index'] = 2_000_000_000_000

        result = self.lending_contract.investLBFinalize(
            address = BOB_ADDRESS,
            initial_lb_shares = 200,
            initial_tzBTC_shares = 5,
            tzBTC2xtz = 0,
        ).run_code(
            amount = 0,
            balance = 0,
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['total_net_credit'], 750_000_000_000)
        self.assertEqual(new_storage['total_gross_credit'], 600_000_000_000)
        self.assertEqual(new_storage['lb_shares'], 300)
        self.assertEqual(new_storage['tzBTC_shares'], 2)

        self.assertDictEqual(new_storage['liquidity_book'], 
            {BOB_ADDRESS: {
                'net_credit': 750_000_000_000,
                'gross_credit': 600_000_000_000,
                'lb_shares': 100,
            }})

        # case non empty initial data
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['totalSupply'] = 100_000_000_000_000
        initial_storage['total_net_credit'] = 250_000_000_000
        initial_storage['total_gross_credit'] = 200_000_000_000

        initial_storage['lb_shares'] = 800
        initial_storage['tzBTC_shares'] = 7

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
            initial_lb_shares = 600,
            initial_tzBTC_shares = 8,
            tzBTC2xtz = 0,
        ).run_code(
            storage = initial_storage,
            sender = self_address,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['total_net_credit'], 500_000_000_000)
        self.assertEqual(new_storage['total_gross_credit'], 400_000_000_000)

        self.assertEqual(new_storage['lb_shares'], 800)
        self.assertEqual(new_storage['tzBTC_shares'], 7)

        self.assertDictEqual(new_storage['liquidity_book'], 
            {BOB_ADDRESS: {
                'net_credit': 500_000_000_000,
                'gross_credit': 400_000_000_000,
                'lb_shares': 300,
            }})

    def test_impossible_cases(self):
        self_address = self.lending_contract.context.get_self_address()

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['lb_shares'] = 100
        initial_storage['tzBTC_shares'] = 200

        # tzBTC delta error
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 80, 180, 0).run_code(storage=initial_storage, sender=self_address)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'negative tzBTC delta error')

        # lb delta error
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 120, 220, 0).run_code(storage=initial_storage, sender=self_address)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'negative lb delta error')

    def test_leverage(self):
        self_address = self.lending_contract.context.get_self_address()

        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = self.dex_contract.context.address
        initial_storage['fa_tzBTC_address'] = self.tzbtc_token.context.address
        initial_storage['fa_lb_address'] = self.lqt_token.context.address

        initial_storage['tzBTC_shares'] = 100_000_000
        initial_storage['totalSupply'] = 300_000_000_000_000_000_000

        # leverage = 4
        with self.assertNotRaises(Exception):
            result = self.lending_contract.investLBFinalize(BOB_ADDRESS, 0, 400_000_000, 100_000_000).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        # leverage > 4
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(BOB_ADDRESS, 0, 400_000_000, 100_000_001).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')

        # changing max leverage with storage to 5
        initial_storage = deepcopy(DEFAULT_STORAGE)
        initial_storage['liquidity_baking_address'] = self.dex_contract.context.address
        initial_storage['fa_tzBTC_address'] = self.tzbtc_token.context.address
        initial_storage['fa_lb_address'] = self.lqt_token.context.address

        initial_storage['tzBTC_shares'] = 100_000_000
        initial_storage['totalSupply'] = 300_000_000_000_000_000_000
        initial_storage['max_leverage'] = 50

        # leverage = 5
        with self.assertNotRaises(Exception):
            result = self.lending_contract.investLBFinalize(BOB_ADDRESS, 0, 400_000_000, 112_500_000).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        # leverage > 5
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(BOB_ADDRESS, 0, 400_000_000, 112_500_001).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'leverage error')

    def test_forbidden_cases(self):
        # admin tries
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 0, 0, 0).run_code(sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # not admin tries
        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(ALICE_ADDRESS, 0, 0, 0).run_code(sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

    def test_totalSupply_net_credit_inequation(self):
        self_address = self.lending_contract.context.get_self_address()

        # ok case
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['tzBTC_shares'] = 1_000

        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 1_500_000_000_000_000

        initial_storage['total_net_credit'] = 0
        initial_storage['net_credit_index'] = 4_000_000_000_000

        with self.assertNotRaises(Exception):
            self.lending_contract.investLBFinalize(
                address = BOB_ADDRESS,
                initial_lb_shares = 0,
                initial_tzBTC_shares = 4_000,
                tzBTC2xtz = 0,
            ).run_code(
                storage = initial_storage,
                sender = self_address,
            )

        # fail case
        initial_storage = deepcopy(DEFAULT_STORAGE)

        initial_storage['tzBTC_shares'] = 1_000

        initial_storage['deposit_index'] = 2_000_000_000_000
        initial_storage['totalSupply'] = 1_500_000_000_000_000 - 1

        initial_storage['total_net_credit'] = 0
        initial_storage['net_credit_index'] = 4_000_000_000_000

        with self.assertRaises(MichelsonError) as context:
            self.lending_contract.investLBFinalize(
                address = BOB_ADDRESS,
                initial_lb_shares = 0,
                initial_tzBTC_shares = 4_000,
                tzBTC2xtz = 0,
            ).run_code(
                storage = initial_storage,
                sender = self_address,
            )
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'total deposit and net credit inequation error')
