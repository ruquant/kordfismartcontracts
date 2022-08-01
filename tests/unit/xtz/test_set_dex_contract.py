from copy import deepcopy


from pytezos.rpc.errors import MichelsonError


from ..base import LendingContractBaseTestCase
from ..constants import ALICE_ADDRESS, BOB_ADDRESS, CONTRACT_ADDRESS
from ..constants import DEFAULT_STORAGE


class SetDexContractEntryUnitTest(LendingContractBaseTestCase):

    def test_basic(self):
        initial_storage = deepcopy(DEFAULT_STORAGE)

        result = self.lending_contract.setDexContract(CONTRACT_ADDRESS).run_code(
            storage = initial_storage,
            sender = ALICE_ADDRESS,
        )

        self.assertEqual(result.storage['dex_contract_address'], CONTRACT_ADDRESS)
        del initial_storage['dex_contract_address']
        del result.storage['dex_contract_address']

        self.assertDictEqual(result.storage, initial_storage)
        self.assertEqual(len(result.operations), 0)

    def test_forbidden_case(self):
        with self.assertRaises(MichelsonError) as context:
            storage = deepcopy(DEFAULT_STORAGE)
            self.lending_contract.setDexContract(CONTRACT_ADDRESS).run_code(storage=storage, sender=BOB_ADDRESS)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')
