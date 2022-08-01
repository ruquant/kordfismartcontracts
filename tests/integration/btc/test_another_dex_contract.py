from pytezos import ContractInterface
from pytezos.crypto.key import Key


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class AnotherDexContractTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'tzBTC_shares': 10_000,
            'totalSupply': 10_000_000_000_000,

            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },
            'deposit_index': 10**15,
            'net_credit_index': 10**18,
            'gross_credit_index': 10**21,

            # no upfront commission
            'upfront_commission': 0,

            'onchain_liquidation_percent': 1_000,  # 1_000%
        }
        super().setUpClass(initial_storage, btc_version=True)

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
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 10_000,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_basic(self):
        main_address = self.main_contract.context.address
        dex_contract_address = self.another_dex_contract.context.address

        # Admin changes DEX contract
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setDexContract(dex_contract_address).send(gas_reserve=10000, min_confirmations=1)

        # Bob invest LB leverage = 1.5
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 50_000_000, 
            mintzBTCTokensBought = 47, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 150_000_000, 
            minLqtMinted = 150_000,
        ).with_amount(200_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 150_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 150_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 9_897)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 9_897)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 103_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 103_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 150_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 103_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 103_000_000)

        self.assertEqual(self.main_contract.context.get_balance(), 0)

        # another dex contract
        self.assertEqual(self.another_dex_contract.storage['tokenPool'](), 953)
        self.assertEqual(self.another_dex_contract.storage['xtzPool'](), 1_049_950_000)

        # lb contract
        self.assertEqual(self.dex_contract.storage['tokenPool'](), 1_150)
        self.assertEqual(self.dex_contract.storage['xtzPool'](), 1_150_000_000)
        self.assertEqual(self.dex_contract.storage['lqtTotal'](), 1_150_000)

        # Bob invest LB leverage = 3
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 48,
            minXtzBought = 50_249_017,
            amount2Lqt = 150_000_000, 
            minLqtMinted = 150_000,
        ).with_amount(100_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 300_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 300_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 9_699)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 9_699)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 301_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 301_000_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 300_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 301_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 301_000_000)

        self.assertEqual(self.main_contract.context.get_balance(), 0)

        # another dex contract
        self.assertEqual(self.another_dex_contract.storage['tokenPool'](), 1_001)
        self.assertEqual(self.another_dex_contract.storage['xtzPool'](), 999_899_450)

        # lb contract
        self.assertEqual(self.dex_contract.storage['tokenPool'](), 1_300)
        self.assertEqual(self.dex_contract.storage['xtzPool'](), 1_300_000_000)
        self.assertEqual(self.dex_contract.storage['lqtTotal'](), 1_300_000)

        # Bob redeems
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLB(300_000, 0, 1_100_000).send(gas_reserve=10000, min_confirmations=1)

        with self.assertRaises(KeyError):
            self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(self.main_contract.storage['lb_shares'](), 0)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 10_000)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 10_000)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        # another dex contract
        self.assertEqual(self.another_dex_contract.storage['tokenPool'](), 1_000)
        self.assertEqual(self.another_dex_contract.storage['xtzPool'](), 1_000_998_350)

        # lb contract
        self.assertEqual(self.dex_contract.storage['tokenPool'](), 1_000)
        self.assertEqual(self.dex_contract.storage['xtzPool'](), 1_000_000_000)
        self.assertEqual(self.dex_contract.storage['lqtTotal'](), 1_000_000)

        # Bob again invest LB and admin liquidates him
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 150_000_000, 
            minLqtMinted = 150_000,
        ).with_amount(150_000_000).send(gas_reserve=10000, min_confirmations=1)

        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.liquidateOnchainLB(BOB_ADDRESS).send(gas_reserve=10000, min_confirmations=1)

        # another dex contract
        self.assertEqual(self.another_dex_contract.storage['tokenPool'](), 870)
        self.assertEqual(self.another_dex_contract.storage['xtzPool'](), 1_150_848_350)

        # lb contract
        self.assertEqual(self.dex_contract.storage['tokenPool'](), 1_000)
        self.assertEqual(self.dex_contract.storage['xtzPool'](), 1_000_000_000)
        self.assertEqual(self.dex_contract.storage['lqtTotal'](), 1_000_000)
