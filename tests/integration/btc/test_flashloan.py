import subprocess
from os.path import dirname, join


from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos import ContractInterface
from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY


FLASHLOANER_SOURCE_FILE = join(dirname(__file__), '../../DummyFlashloaner.py')
FLASHLOANER_OUT_DIR = join(dirname(__file__), '../../../.out_flashloaner')
FLASHLOANER_COMPILE_COMMAND = '''\
    ~/smartpy-cli/SmartPy.sh compile {source_file} {out_dir} --protocol ithaca
'''.format(
    source_file = FLASHLOANER_SOURCE_FILE,
    out_dir = FLASHLOANER_OUT_DIR,
)

class FlashLoanTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },

            'deposit_index': 1_700_000_000_000,
        }
        super().setUpClass(initial_storage, btc_version=True)

        # originating flashloaner
        p = subprocess.run(FLASHLOANER_COMPILE_COMMAND, shell=True)
        assert p.returncode == 0, 'Contract compilation should be successfull.'

        context = ExecutionContext(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key=Key.from_encoded_key(ALICE_KEY),
        )

        cls.flash_loaner = ContractInterface.from_file(
            join(FLASHLOANER_OUT_DIR, 'contract/step_000_cont_0_contract.tz'),
            context,
        )

        result = cls.flash_loaner.originate(
            initial_storage={
                'kord_contract': cls.main_contract.context.address,
                'fa_tzBTC_address': cls.tzbtc_token.context.address,
                'return_amount': 0,
                'balance': 0,
                'return_shares': 0,
                'tzBTC_shares': 0,
            }).send(gas_reserve=10000, min_confirmations=1)

        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        cls.flash_loaner.context.address = originated_address

        cls.bob_client.bulk(
            cls.tzbtc_token.approve(value=10**7, spender=cls.main_contract.address),
            cls.main_contract.depositLending(10**7),
            cls.tzbtc_token.approve(value=0, spender=cls.main_contract.address),
            cls.tzbtc_token.transfer(**{
                'from': BOB_ADDRESS,
                'to': cls.flash_loaner.context.address,
                'value': 1_000_000,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_basic(self):
        with self.assertRaises(MichelsonError) as context:
            self.flash_loaner.context.key = Key.from_encoded_key(BOB_KEY)
            self.flash_loaner.try_flashloan_btc(100, 0).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'flashloan is not available')

        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.setFlashloanParams(0, 0, True).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setFlashloanParams(123, 456, True).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.main_contract.storage['flashloan_admin_commission'](), 123)
        self.assertEqual(self.main_contract.storage['flashloan_deposit_commission'](), 456)
        self.assertTrue(self.main_contract.storage['flashloan_available']())

        with self.assertRaises(MichelsonError) as context:
            self.flash_loaner.context.key = Key.from_encoded_key(BOB_KEY)
            self.flash_loaner.try_flashloan_btc(10_057_899, 10_000_000).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'loan error')

        self.flash_loaner.context.key = Key.from_encoded_key(BOB_KEY)
        self.flash_loaner.try_flashloan_btc(10_057_900, 10_000_000).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.flash_loaner.storage['tzBTC_shares'](), 11_000_000)
        self.assertEqual(self.tzbtc_token.storage['tokens'][self.flash_loaner.context.address](), 942_100)

        contract_tokens = self.tzbtc_token.storage['tokens'][self.main_contract.context.address]()
        self.assertEqual(contract_tokens, 10_057_900)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 10_057_900)

        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_707_752_000_000)
