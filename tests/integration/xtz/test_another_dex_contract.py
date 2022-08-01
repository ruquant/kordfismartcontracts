from pytezos import ContractInterface
from pytezos.crypto.key import Key


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class AnotherDexContractTest(MainContractBaseTestCase):

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
            'deposit_index': 10**12,
            'net_credit_index': 10**15,
            'gross_credit_index': 10**18,

            # no upfront commission
            'upfront_commission': 0,

            'onchain_liquidation_percent': 1_000,  # 1_000%
        }
        super().setUpClass(initial_storage, btc_version=False)

        # originate another dex contract
        cls.another_dex_contract = ContractInterface.from_file(cls.dex_path, cls.context)
        result = cls.another_dex_contract.originate(
          initial_storage=cls.initial_dex_storage,
          balance=10 ** 9,
        ).send(gas_reserve=10000, min_confirmations=1)
        originated_address = result.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]
        cls.another_dex_contract.context.address = originated_address

        cls.alice_client.bulk(
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.another_dex_contract.context.address,
                'value': 1_000,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_basic(self):
        main_address = self.main_contract.context.address
        dex_contract_address = self.another_dex_contract.context.address

        # Admin changes DEX contract
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setDexContract(dex_contract_address).send(gas_reserve=10000, min_confirmations=1)

        # Bob deposits 200 xtz
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending().with_amount(2 * 10**8).send(gas_reserve=10000, min_confirmations=1)

        # Bob invest LB leverage up to 1.5
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 15_258_930,
            mintzBTCTokensBought = 15,
            amount2Lqt = 14_429_860,
            minLqtMinted = 14_429,
            tzBTCShares = 0,
        ).with_amount(20_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 14_429)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 14_429)

        self.assertEqual(self.main_contract.context.get_balance(), 190_311_210)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 9_688_790)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 9_688_790_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 14_429)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 9_688_790)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 9_688_790_000)

        # another dex contract
        self.assertEqual(self.another_dex_contract.storage['tokenPool'](), 985)
        self.assertEqual(self.another_dex_contract.storage['xtzPool'](), 1_015_243_671)

        # lb contract
        self.assertEqual(self.dex_contract.storage['tokenPool'](), 1_015)
        self.assertEqual(self.dex_contract.storage['xtzPool'](), 1_014_429_860)
        self.assertEqual(self.dex_contract.storage['lqtTotal'](), 1_014_429)

        # Bob redeems
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(14_429, 0).send(gas_reserve=10000, min_confirmations=1)

        with self.assertRaises(KeyError):
            self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(self.main_contract.storage['lb_shares'](), 0)

        self.assertEqual(self.main_contract.context.get_balance(), 200_000_000)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        # another dex contract
        self.assertEqual(self.another_dex_contract.storage['tokenPool'](), 999)
        self.assertEqual(self.another_dex_contract.storage['xtzPool'](), 1_001_030_061)

        # lb contract
        self.assertEqual(self.dex_contract.storage['tokenPool'](), 1_001)
        self.assertEqual(self.dex_contract.storage['xtzPool'](), 1_000_000_848)
        self.assertEqual(self.dex_contract.storage['lqtTotal'](), 1_000_000)

        # Bob again invest LB and admin liquidates him
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 17_000_000,
            mintzBTCTokensBought = 0,
            amount2Lqt = 15_000_000,
            minLqtMinted = 0,
            tzBTCShares = 0,
        ).with_amount(15_000_000).send(gas_reserve=10000, min_confirmations=1)

        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.liquidateOnchainLB(BOB_ADDRESS).send(gas_reserve=10000, min_confirmations=1)

        # another dex contract
        self.assertEqual(self.another_dex_contract.storage['tokenPool'](), 998)
        self.assertEqual(self.another_dex_contract.storage['xtzPool'](), 1_002_727_335)

        # lb contract
        self.assertEqual(self.dex_contract.storage['tokenPool'](), 1_002)
        self.assertEqual(self.dex_contract.storage['xtzPool'](), 1_000_001_821)
        self.assertEqual(self.dex_contract.storage['lqtTotal'](), 1_000_000)
