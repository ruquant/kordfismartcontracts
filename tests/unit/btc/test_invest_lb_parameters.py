from unittest import TestCase

from ...tzbtc_invest_params import get_client_invest_params


class InvestParamsLeverageOneTest(TestCase):
    def test_leverage_one(self):
        amount, xtz_to_convert, minTokens, tzBTC2xtz, minXtz, xtz2lqt, lqtMinted = get_client_invest_params(
            1013765, 32659606961, 12864327, 1000000000, 1, 1)
        self.assertEqual(amount, 1_000_000_000)
        self.assertEqual(xtz_to_convert, 496724840)
        self.assertEqual(xtz2lqt, 503210306)

    def test_leverage_almost_one(self):
        amount, xtz_to_convert, minTokens, tzBTC2xtz, minXtz, xtz2lqt, lqtMinted = get_client_invest_params(
            1013765, 32659606961, 12864327, 1000000000, 1.001, 1)
        self.assertEqual(amount, 1_000_000_000)
        self.assertEqual(xtz_to_convert, 499495052)
        self.assertEqual(xtz2lqt, 500494950)
