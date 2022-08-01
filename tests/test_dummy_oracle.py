from .integration.base import MainContractBaseTestCase


class DummyOracleXtzContractTest(MainContractBaseTestCase):
    def test_dummy_oracle(self):
        self.assertEqual(self.oracle.get_price('XTZ').onchain_view(), 1_530_000)
        self.assertEqual(self.oracle.get_price('BTC').onchain_view(), 45_500_000_000)

        self.oracle.set_price(xtz_price=2_530_000, btc_price=25_500_000_000).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.oracle.get_price('XTZ').onchain_view(), 2_530_000)
        self.assertEqual(self.oracle.get_price('BTC').onchain_view(), 25_500_000_000)

class DummyOracleBtcContractTest(MainContractBaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass({}, btc_version=True)

    def test_dummy_oracle(self):
        self.assertEqual(self.oracle.get_price('XTZ').onchain_view(), 1_530_000)
        self.assertEqual(self.oracle.get_price('BTC').onchain_view(), 45_500_000_000)

        self.oracle.set_price(xtz_price=2_530_000, btc_price=25_500_000_000).send(gas_reserve=10000, min_confirmations=1)
        self.assertEqual(self.oracle.get_price('XTZ').onchain_view(), 2_530_000)
        self.assertEqual(self.oracle.get_price('BTC').onchain_view(), 25_500_000_000)
