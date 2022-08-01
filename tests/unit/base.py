from os.path import dirname, join
import subprocess
from unittest import TestCase


from contextlib import contextmanager
from pytezos import ContractInterface
from pytezos.context.impl import ExecutionContext
from pytezos.rpc import RpcNode, ShellQuery
from pytezos.crypto.key import Key
from pytezos.crypto.encoding import base58_encode, base58_decode

from pytezos.contract.result import ContractCallResult
from pytezos.michelson.sections.storage import StorageSection
from pytezos.operation.content import format_mutez, format_tez

from .contracts import get_xtz_compiled_filepath, get_btc_compiled_filepath, get_demo_lb_contracts
from .constants import ALICE_KEY, ALICE_ADDRESS


# This code was patched for 'now' parameter.
def run_code_patched(
    self,
    storage=None,
    source=None,
    sender=None,
    amount=None,
    balance=None,
    chain_id=None,
    gas_limit=None,
    now=None,
) -> ContractCallResult:
    """Execute using RPC interpreter.

    :param storage: initial storage as Python object, leave None if you want to generate a dummy one
    :param source: patch SOURCE
    :param sender: patch SENDER
    :param amount: patch AMOUNT
    :param balance: patch BALANCE
    :param chain_id: patch CHAIN_ID
    :param gas_limit: restrict max consumed gas
    :rtype: ContractCallResult
    """
    storage_ty = StorageSection.match(self.context.storage_expr)
    if storage is None:
        initial_storage = storage_ty.dummy(self.context).to_micheline_value(lazy_diff=True)
    else:
        initial_storage = storage_ty.from_python_object(storage).to_micheline_value(lazy_diff=True)
    script = [self.context.parameter_expr, self.context.storage_expr, self.context.code_expr]

    def skip_nones(**kwargs) -> dict:
        return {k: v for k, v in kwargs.items() if v is not None}

    query = skip_nones(
        script=script,
        storage=initial_storage,
        entrypoint=self.parameters['entrypoint'],
        input=self.parameters['value'],
        amount=format_mutez(amount or self.amount),
        chain_id=chain_id or self.context.get_chain_id(),
        source=sender,
        payer=source,
        balance=str(balance or 0),
        gas=str(gas_limit) if gas_limit is not None else None,
        now=(str(now) if now is not None else None),
    )
    res = self.shell.blocks[self.block_id].helpers.scripts.run_code.post(query)
    return ContractCallResult.from_run_code(res, parameters=self.parameters, context=self.context)


class LendingContractBaseTestCase(TestCase):
    """
        This class allows using demo_lb contracts.
    """
    @classmethod
    def setUpClass(cls, btc_version = False):
        super().setUpClass()
        cls.btc_version = btc_version
        contracts = get_demo_lb_contracts()
        cls.dex_contract = contracts['dex_contract']
        cls.another_dex_contract = contracts['another_dex_contract']
        cls.tzbtc_token = contracts['tzbtc_token']
        cls.lqt_token = contracts['lqt_token']
        cls.oracle = contracts['oracle']

    def setUp(self):
        context = ExecutionContext(
            shell = ShellQuery(RpcNode('http://localhost:20000')),
            key = Key.from_encoded_key(ALICE_KEY),
        )
        self.lending_contract = ContractInterface.from_file(
            get_btc_compiled_filepath() if self.btc_version else get_xtz_compiled_filepath(),
            context,
        )

    def assertAddressFromBytesEquals(self, hex_encoded_address, base58_encoded_address):
        decoded_address = base58_decode(base58_encoded_address.encode()).hex()
        if hex_encoded_address.startswith('0000'):
            self.assertEqual(hex_encoded_address[4:44], decoded_address)
        else:
            self.assertEqual(hex_encoded_address[2:42], decoded_address)

    @contextmanager
    def assertNotRaises(self, exc_type):
        try:
            yield None
        except exc_type:
            raise self.failureException('{} raised'.format(exc_type.__name__))
