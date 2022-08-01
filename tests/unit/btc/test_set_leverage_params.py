from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, CONTRACT_ADDRESS
from ..constants import BTC_DEFAULT_STORAGE as DEFAULT_STORAGE


class SetLeverageParamsEntryUnitTest(LendingContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass(btc_version=True)

    def test_basic(self):
        # case normal: 50, 130, 60
        initial_storage = deepcopy(DEFAULT_STORAGE)
        result = self.lending_contract.setLeverageParams(50, 130, 60, 120, 110, 50, CONTRACT_ADDRESS).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['max_leverage'], 50)
        del initial_storage['max_leverage']
        del new_storage['max_leverage']

        self.assertEqual(new_storage['onchain_liquidation_percent'], 130)
        del initial_storage['onchain_liquidation_percent']
        del new_storage['onchain_liquidation_percent']

        self.assertEqual(new_storage['onchain_liquidation_comm'], 60)
        del initial_storage['onchain_liquidation_comm']
        del new_storage['onchain_liquidation_comm']
  
        self.assertEqual(new_storage['oracle_address'], CONTRACT_ADDRESS)
        del initial_storage['oracle_address']
        del new_storage['oracle_address']

        self.assertDictEqual(new_storage, initial_storage)

        # case 2: 40, 110, 30
        initial_storage = deepcopy(DEFAULT_STORAGE)
        result = self.lending_contract.setLeverageParams(40, 110, 30, 120, 110, 50, CONTRACT_ADDRESS).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['max_leverage'], 40)
        del initial_storage['max_leverage']
        del new_storage['max_leverage']

        self.assertEqual(new_storage['onchain_liquidation_percent'], 110)
        del initial_storage['onchain_liquidation_percent']
        del new_storage['onchain_liquidation_percent']

        self.assertEqual(new_storage['onchain_liquidation_comm'], 30)
        del initial_storage['onchain_liquidation_comm']
        del new_storage['onchain_liquidation_comm']
  
        self.assertEqual(new_storage['oracle_address'], CONTRACT_ADDRESS)
        del initial_storage['oracle_address']
        del new_storage['oracle_address']

        self.assertDictEqual(new_storage, initial_storage)

        # max available values
        initial_storage = deepcopy(DEFAULT_STORAGE)
        result = self.lending_contract.setLeverageParams(100, 200, 100, 120, 110, 50, CONTRACT_ADDRESS).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['max_leverage'], 100)
        del initial_storage['max_leverage']
        del new_storage['max_leverage']

        self.assertEqual(new_storage['onchain_liquidation_percent'], 200)
        del initial_storage['onchain_liquidation_percent']
        del new_storage['onchain_liquidation_percent']

        self.assertEqual(new_storage['onchain_liquidation_comm'], 100)
        del initial_storage['onchain_liquidation_comm']
        del new_storage['onchain_liquidation_comm']

        self.assertEqual(new_storage['oracle_address'], CONTRACT_ADDRESS)
        del initial_storage['oracle_address']
        del new_storage['oracle_address']

        self.assertDictEqual(new_storage, initial_storage)

        # min available values
        initial_storage = deepcopy(DEFAULT_STORAGE)
        result = self.lending_contract.setLeverageParams(20, 101, 0, 120, 110, 50, CONTRACT_ADDRESS).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )
        new_storage = deepcopy(result.storage)

        self.assertEqual(len(result.operations), 0)

        self.assertEqual(new_storage['max_leverage'], 20)
        del initial_storage['max_leverage']
        del new_storage['max_leverage']

        self.assertEqual(new_storage['onchain_liquidation_percent'], 101)
        del initial_storage['onchain_liquidation_percent']
        del new_storage['onchain_liquidation_percent']

        self.assertEqual(new_storage['onchain_liquidation_comm'], 0)
        del initial_storage['onchain_liquidation_comm']
        del new_storage['onchain_liquidation_comm']

        self.assertEqual(new_storage['oracle_address'], CONTRACT_ADDRESS)
        del initial_storage['oracle_address']
        del new_storage['oracle_address']

        self.assertDictEqual(new_storage, initial_storage)

    def test_bad_params(self):
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setLeverageParams(19, 130, 60, 120, 110, 50, CONTRACT_ADDRESS).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'max_leverage min value error')

        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setLeverageParams(101, 130, 60, 120, 110, 50, CONTRACT_ADDRESS).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'max_leverage max value error')

        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setLeverageParams(50, 100, 60, 120, 110, 50, CONTRACT_ADDRESS).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'onchain_liquidation_percent min value error')

        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setLeverageParams(50, 201, 60, 120, 110, 50, CONTRACT_ADDRESS).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'onchain_liquidation_percent max value error')

        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setLeverageParams(50, 130, 101, 120, 110, 50, CONTRACT_ADDRESS).run_code(storage=storage, sender=ALICE_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'onchain_liquidation_comm max value error')

    def test_forbidden_case(self):
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setLeverageParams(50, 130, 60, 120, 110, 50, CONTRACT_ADDRESS).run_code(storage=storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
