import subprocess
from decimal import Decimal
from datetime import timedelta, datetime
from os.path import dirname, join

from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos import ContractInterface
from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError

from ..base import MainContractBaseTestCase
from ...constants import ALICE_KEY, ALICE_ADDRESS, BOB_KEY, BOB_ADDRESS, CLARE_ADDRESS, CLARE_KEY, TEST_GAS_DELTA

VIEWER_SOURCE_FILE = join(dirname(__file__), '../../DummyViewer.py')
VIEWER_OUT_DIR = join(dirname(__file__), '../../../.out_viewer')
VIEWER_COMPILE_COMMAND = '''\
    ~/smartpy-cli/SmartPy.sh compile {source_file} {out_dir} --protocol ithaca
'''.format(
    source_file = VIEWER_SOURCE_FILE,
    out_dir = VIEWER_OUT_DIR,
)

class FA12Test(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        # originate viewer contract
        p = subprocess.run(VIEWER_COMPILE_COMMAND, shell=True)
        assert p.returncode == 0, 'Viewer contract compilation should be successfull.'
        context = ExecutionContext(
            shell=ShellQuery(RpcNode('http://localhost:20000')),
            key=Key.from_encoded_key(ALICE_KEY),
        )
        cls.viewer = ContractInterface.from_file(
            join(VIEWER_OUT_DIR, 'contract/step_000_cont_0_contract.tz'),
            context,
        )
        result = cls.viewer.originate(
            initial_storage=None).send(gas_reserve=10000, min_confirmations=1)
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        cls.viewer.context.address = originated_address

        # main contract
        initial_storage = {}
        initial_storage['deposit_index'] = 1_500_000_000_000
        initial_storage['net_credit_index'] = 1_700_000_000_000
        initial_storage['gross_credit_index'] = 1_800_000_000_000
        super().setUpClass(initial_storage, btc_version=True)

    def test_common_operations(self):
        # Bob deposits and gets tokens
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.bob_client.bulk(
            self.tzbtc_token.approve(
                value = 10**7,
                spender = self.main_contract.address,
            ),
            self.main_contract.depositLending(10_000_000),
            self.main_contract.getBalance(BOB_ADDRESS, f'{self.viewer.context.address}%target')
        ).send(gas_reserve=10000, min_confirmations=1)

        self.assertEqual(self.viewer.storage(), 6_666_666_666_666_666_666)
        self.assertDictEqual(self.main_contract.storage['ledger'][BOB_ADDRESS](),
            {'balance': 6_666_666_666_666_666_666, 'approvals': {}})

        # Bob sends some tokens to Clare
        self.bob_client.bulk(
            self.main_contract.transfer(**{
                'from': BOB_ADDRESS,
                'to': CLARE_ADDRESS,
                'value': 150_000_000_000_000_000,
            }),
            self.main_contract
                .getBalance(CLARE_ADDRESS, f'{self.viewer.context.address}%target')
        ).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.viewer.storage(), 150_000_000_000_000_000)
        self.assertDictEqual(self.main_contract.storage['ledger'][BOB_ADDRESS](),
            {'balance': 6_516_666_666_666_666_666, 'approvals': {}})
        self.assertDictEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS](),
            {'balance': 150_000_000_000_000_000, 'approvals': {}})

        # Clare can withdraw deposit
        self.main_contract.context.key = Key.from_encoded_key(CLARE_KEY)
        self.main_contract.redeemLending(100_000).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.tzbtc_token.storage['tokens'][CLARE_ADDRESS](), 100_000)
        self.assertDictEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS](),
            {'balance': 83_333_333_333_333_333, 'approvals': {}})
        self.assertDictEqual(self.main_contract.storage['ledger'][BOB_ADDRESS](),
            {'balance': 6_516_666_666_666_666_666, 'approvals': {}})

        # Bob approves token to spend and Clare spends Bobs tokens
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.approve(
            value = 200_000_000_000_000_000,
            spender = CLARE_ADDRESS,
        ).send(gas_reserve=10000, min_confirmations=1)
        self.main_contract.context.key = Key.from_encoded_key(CLARE_KEY)
        self.main_contract.transfer(**{
            'from': BOB_ADDRESS,
            'to': ALICE_ADDRESS,
            'value': 150_000_000_000_000_000,
        }).send(gas_reserve=10000, min_confirmations=1)
        self.assertDictEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS](),
            {'balance': 83_333_333_333_333_333, 'approvals': {}})
        self.assertDictEqual(self.main_contract.storage['ledger'][BOB_ADDRESS](),
            {'balance': 6_366_666_666_666_666_666, 'approvals': { CLARE_ADDRESS: 50_000_000_000_000_000}})
        self.assertDictEqual(self.main_contract.storage['ledger'][ALICE_ADDRESS](),
            {'balance': 150_000_000_000_000_000, 'approvals': {}})

        # Check errors
        # Admin can not transfer Bob deposit
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
            self.main_contract.transfer(**{
                'from': BOB_ADDRESS,
                'to': ALICE_ADDRESS,
                'value': 6_000_000_000_000_000_000,
            }).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'NotEnoughAllowance')

        # Try to spend more than allowed
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(CLARE_KEY)
            self.main_contract.transfer(**{
                'from': BOB_ADDRESS,
                'to': ALICE_ADDRESS,
                'value': 150_000_000_000_000_000,
            }).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'NotEnoughAllowance')

        # Try to spend more than balance
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.transfer(**{
                'from': BOB_ADDRESS,
                'to': ALICE_ADDRESS,
                'value': 7_000_000_000_000_000_000,
            }).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'NotEnoughBalance')

        self.assertDictEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS](),
            {'balance': 83_333_333_333_333_333, 'approvals': {}})
        self.assertDictEqual(self.main_contract.storage['ledger'][BOB_ADDRESS](),
            {'balance': 6_366_666_666_666_666_666, 'approvals': { CLARE_ADDRESS: 50_000_000_000_000_000}})
        self.assertDictEqual(self.main_contract.storage['ledger'][ALICE_ADDRESS](),
            {'balance': 150_000_000_000_000_000, 'approvals': {}})

        # Change approve from nonzero to nonzero is not allowed
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.approve(
                value = 200_000_000_000_000_000,
                spender = CLARE_ADDRESS,
            ).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'UnsafeAllowanceChange')
