from pytezos.crypto.key import Key


from ..base import MainContractBaseTestCase
from ...constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY


class BasicTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        initial_storage = {
            'deposit_index': 10**15,
            'net_credit_index': 10**18,
            'gross_credit_index': 10**21,

            # no upfront commission
            'upfront_commission': 0,
        }
        super().setUpClass(initial_storage, btc_version=True)

    def test_with_zero_rates(self):
        main_address = self.main_contract.context.address

        # set rate params to 0 so all indexes will be permanently equal to their initial values
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.setRateParams(
            rate_1 = 0,
            rate_diff = 0,
            threshold_percent_1 = 0,
            threshold_percent_2 = 100,
        ).send(gas_reserve=10000, min_confirmations=1)

        # Bob deposits 0.1 BTC
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 10**7,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending(10**7).send(gas_reserve=10000, min_confirmations=1)

        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 0,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        bob_tokens = self.tzbtc_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_tokens, 90_000_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 10_000_000)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 10_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 10_000_000_000_000_000)
        with self.assertRaises(KeyError):
            self.main_contract.storage['liquidity_book'][BOB_ADDRESS]()

        self.assertEqual(self.main_contract.storage['lb_shares'](), 0)

        # Bob deposits more 0.2 BTC
        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 2 * 10**7,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.depositLending(2 * 10**7).send(gas_reserve=10000, min_confirmations=1)
        
        bob_tokens = self.tzbtc_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_tokens, 70_000_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 30_000_000)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 30_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 30_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['lb_shares'](), 0)

        self.tzbtc_token.context.key = Key.from_encoded_key(BOB_KEY)
        self.tzbtc_token.approve(
            value = 0,
            spender = self.main_contract.address,
        ).send(gas_reserve=10000, min_confirmations=1)

        # Bob redeems 0.05 BTC
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.redeemLending(5 * 10**6).send(gas_reserve=10000, min_confirmations=1)

        bob_tokens = self.tzbtc_token.storage['tokens'][BOB_ADDRESS]()
        self.assertEqual(bob_tokens, 75_000_000)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 25_000_000)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 25_000_000)

        self.assertEqual(self.main_contract.storage['ledger'][BOB_ADDRESS]['balance'](), 25_000_000_000_000_000)

        self.assertEqual(self.main_contract.storage['lb_shares'](), 0)

        self.assertEqual(self.main_contract.context.get_balance(), 0)

        # Bob invests LB leverage = 2

        # DEX storage:
        # tokenPool 10^3
        # xtzPool 10^9
        # lqtTotal 10^6
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 200_000_000, 
            minLqtMinted = 0,
        ).with_amount(200_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 24_999_800)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 24_999_800)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 200_000)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 200_000)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 200_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 200_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 200_000_000)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 200_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 200_000_000)

        # Alice invests LB leverage = 1.5
        # FIXME: let somebody (not admin or Bob) do it

        # DEX storage:
        # tokenPool 1.2 * 10^3
        # xtzPool 1.2 * 10^9
        # lqtTotal 1.2 * 10^6
        self.main_contract.context.key = Key.from_encoded_key(ALICE_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 100_000_000, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 0,
            minXtzBought = 0,
            amount2Lqt = 300_000_000, 
            minLqtMinted = 0,
        ).with_amount(400_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 24_999_636)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 24_999_636)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 476_944)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 476_944)

        # we made all indexes unchangable with setParams
        self.assertEqual(self.main_contract.storage['deposit_index'](), 10**15)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 10**18)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 10**21)

        self.assertEqual(self.main_contract.storage['liquidity_book'][ALICE_ADDRESS]['lb_shares'](), 276_944)
        self.assertEqual(self.main_contract.storage['liquidity_book'][ALICE_ADDRESS]['gross_credit'](), 164_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][ALICE_ADDRESS]['net_credit'](), 164_000_000)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 364_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 364_000_000)

        self.assertEqual(self.main_contract.context.get_balance(), 0)

        # Bob invests LB leverage = 2.5

        # DEX storage:
        # tokenPool 1_364
        # xtzPool 1_599_900_000
        # lqtTotal 1_476_944
        self.main_contract.context.key = Key.from_encoded_key(BOB_KEY)
        self.main_contract.investLB(
            amount2tzBTC = 0, 
            mintzBTCTokensBought = 0, 
            tzBTC2xtz = 50,
            minXtzBought = 50_000_000,
            amount2Lqt = 250_000_000, 
            minLqtMinted = 0,
        ).with_amount(200_000_000).send(gas_reserve=10000, min_confirmations=1)

        contract_tokens = self.tzbtc_token.storage['tokens'][main_address]()
        self.assertEqual(contract_tokens, 24_999_361)
        self.assertEqual(self.main_contract.storage['tzBTC_shares'](), 24_999_361)

        contract_lb_tokens = self.lqt_token.storage['tokens'][main_address]()
        self.assertEqual(contract_lb_tokens, 716_182)
        self.assertEqual(self.main_contract.storage['lb_shares'](), 716_182)

        # we made all indexes unchangable with setParams
        self.assertEqual(self.main_contract.storage['deposit_index'](), 10**15)
        self.assertEqual(self.main_contract.storage['net_credit_index'](), 10**18)
        self.assertEqual(self.main_contract.storage['gross_credit_index'](), 10**21)

        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['lb_shares'](), 439_238)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['gross_credit'](), 475_000)
        self.assertEqual(self.main_contract.storage['liquidity_book'][BOB_ADDRESS]['net_credit'](), 475_000_000)

        self.assertEqual(self.main_contract.storage['total_gross_credit'](), 639_000)
        self.assertEqual(self.main_contract.storage['total_net_credit'](), 639_000_000)

        self.assertEqual(self.main_contract.context.get_balance(), 0)
