from pytezos.crypto.key import Key
from pytezos.rpc.errors import MichelsonError


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class LiquidateOnchainLBTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'lb_shares': 130_000,
            'tzBTC_shares': 1_480,

            'deposit_index': 1_500_000_000_000,
            'net_credit_index': 1_600_000_000_000,
            'gross_credit_index': 1_900_000_000_000,

            'total_gross_credit': 1_200_000_000_000_000,
            'total_net_credit': 1_400_000_000_000_000,
            'totalSupply': 4_000_000_000_000_000,

            'ledger': {
                BOB_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
                CLARE_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
            },
            'liquidity_book': {
                BOB_ADDRESS: {
                    'net_credit': 10_000_000_000_000,
                    'gross_credit': 83_000_000_000_000,
                    'lb_shares': 100_000,
                },
                CLARE_ADDRESS: {
                    'net_credit': 300_000_000_000_000,
                    'gross_credit': 200_000_000_000_000,
                    'lb_shares': 30_000,
                },
            },

            'upfront_commission': 1_500,  # 1.5%

            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },
        }

        super().setUpClass(initial_storage, btc_version=True)

        cls.alice_client.bulk(
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 1_480,
            }),
            cls.lqt_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 130_000,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_basic(self):
        main_address = self.main_contract.context.address
        oracle_address = self.oracle.address

        # Bob tries to change commission
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.setLeverageParams(40, 120, 30, 120, 110, 50, oracle_address).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # Admin changes commission to 70%
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setLeverageParams(40, 120, 70, 120, 110, 50, oracle_address).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.main_contract.storage['onchain_liquidation_comm'](), 70)

        # Admin liqudates Bob (extra_shares > 0)
        initial_admin_tzBTC_shares = self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]()
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.liquidateOnchainLB(BOB_ADDRESS).send(gas_reserve=10000, min_confirmations=1)       

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 1_117_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_390_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 1_900_000_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_600_000_000_000)
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_502_500_000_000)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 30_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 30_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 1_648)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 1_648)

        self.assertEqual(self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]() - initial_admin_tzBTC_shares, 21)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 30_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 200_000_000_000_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 300_000_000_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 2_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 2_000_000_000_000_000)

        # Admin liqudates Clare (extra_shares < 0)
        initial_admin_tzBTC_shares = self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]()
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.liquidateOnchainLB(CLARE_ADDRESS).send(gas_reserve=10000, min_confirmations=1)   

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 917_000_000_000_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 1_090_000_000_000_000)
        self.assertEqual(self.main_contract.storage['totalSupply'](), 4_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 1_900_000_000_000)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 1_600_000_000_000)
        self.assertEqual(self.main_contract.storage['deposit_index'](), 1_420_750_000_000)

        with self.assertRaises(KeyError):
            self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(self.main_contract.storage['lb_shares'](), 0)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 1_701)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 1_701)

        self.assertEqual(self.tzbtc_token.storage['tokens'][ALICE_ADDRESS]() - initial_admin_tzBTC_shares, 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['lb_shares'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['gross_credit'](), 0)
        self.assertEqual(self.main_contract.storage['liquidity_book'][CLARE_ADDRESS]['net_credit'](), 0)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 2_000_000_000_000_000)
        self.assertEqual(self.main_contract.storage['ledger'][CLARE_ADDRESS]['balance'](), 2_000_000_000_000_000)

        # Bob tries to disable onchain liquidation
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
            self.main_contract.disableOnchainLiquidation().send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Forbidden.')

        # Admin disables onchain liquidation
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.disableOnchainLiquidation().send(gas_reserve=10000, min_confirmations=1)

        # Admin tries to liquidate after disabling
        with self.assertRaises(MichelsonError) as context:
            self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
            self.main_contract.liquidateOnchainLB(BOB_ADDRESS).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(str(context.exception.args[0]['with']['string']), 'Onchain liquidation disabled.')


class LiquidateOnchainLBWithDisabledStatusTest(MainContractBaseTestCase):

    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'lb_shares': 130_000,
            'tzBTC_shares': 1_480,

            'deposit_index': 1_500_000_000_000,
            'net_credit_index': 1_600_000_000_000,
            'gross_credit_index': 1_900_000_000_000,

            'total_gross_credit': 1_200_000_000_000_000,
            'total_net_credit': 1_400_000_000_000_000,
            'totalSupply': 4_000_000_000_000_000,

            'ledger': {
                BOB_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
                CLARE_ADDRESS: {
                    'balance': 2_000_000_000_000_000,
                    'approvals': {},
                },
            },
            'liquidity_book': {
                BOB_ADDRESS: {
                    'net_credit': 10_000_000_000_000,
                    'gross_credit': 83_000_000_000_000,
                    'lb_shares': 100_000,
                },
                CLARE_ADDRESS: {
                    'net_credit': 300_000_000_000_000,
                    'gross_credit': 200_000_000_000_000,
                    'lb_shares': 30_000,
                },
            },

            'upfront_commission': 1_500,  # 1.5%
            'is_working': False,

            # set rate params to 0 so all indexes will be permanently equal to their initial values
            'rate_params': {
                'rate_1': 0,
                'rate_diff': 0,
                'threshold_percent_1': 0,
                'threshold_percent_2': 100,
            },
        }

        super().setUpClass(initial_storage, btc_version=True)

        cls.alice_client.bulk(
            cls.tzbtc_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 1_480,
            }),
            cls.lqt_token.transfer(**{
                'from': ALICE_ADDRESS,
                'to': cls.main_contract.context.address,
                'value': 130_000,
            }),
        ).send(gas_reserve=10000, min_confirmations=1)

    def test_onchain_liquidation_with_disabled_status(self):
        LiquidateOnchainLBTest.test_basic(self)
