from unittest import TestCase
from .xtz_invest_params import get_invest_params, Contract, get_lb_tokens_value


class SimpleStorageTestCase(TestCase):
    def setUp(self):
        self.contract = Contract(
            1_000,
            1_000_000_000,
            1_000_000,
        )

    def test_xtz_to_token(self):
        self.assertEqual(
            self.contract.xtz_to_token_result(250_000_000),
            199,
        )
        self.assertEqual(self.contract.tokenPool, 801)
        self.assertEqual(self.contract.xtzPool, 1_249_750_000)
        self.assertEqual(self.contract.lqtTotal, 1_000_000)

    def test_add_liquidity(self):
        self.assertEqual(
            self.contract.add_liquidity_result(250_000_000),
            250,
        )
        self.assertEqual(self.contract.tokenPool, 1_250)
        self.assertEqual(self.contract.xtzPool, 1_250_000_000)
        self.assertEqual(self.contract.lqtTotal, 1_250_000)

    def test_invest_result(self):
        invest_amount = 500_000_000
        xtz2token, _, xtz2lqt, _ = get_invest_params(
            self.contract.tokenPool,
            self.contract.xtzPool,
            self.contract.lqtTotal,
            invest_amount,
        )

        max_deposited = self.contract.xtz_to_token_result(xtz2token)
        deposited = self.contract.add_liquidity_result(xtz2lqt)
        self.assertEqual(max_deposited, 183)
        self.assertEqual(deposited, 183)
        self.assertEqual(xtz2token, 225_541_275)
        self.assertEqual(xtz2lqt, 272_958_952)

    def test_invest_result_is_minimal(self):
        invest_amount = 500_000_000
        xtz2token, _, xtz2lqt, _ = get_invest_params(
            self.contract.tokenPool,
            self.contract.xtzPool,
            self.contract.lqtTotal,
            invest_amount,
        )

        max_deposited = self.contract.xtz_to_token_result(xtz2token)
        deposited = self.contract.add_liquidity_result(xtz2lqt - 1)
        self.assertEqual(max_deposited, 183)
        self.assertEqual(deposited, 182)

    def test_invest_result_has_maximum_value(self):
        invest_amount = 500_000_000
        xtz2token, _, xtz2lqt, _ = get_invest_params(
            self.contract.tokenPool,
            self.contract.xtzPool,
            self.contract.lqtTotal,
            invest_amount,
        )

        max_deposited = self.contract.xtz_to_token_result(xtz2token - 1)
        deposited = self.contract.add_liquidity_result(invest_amount - xtz2token + 1)
        self.assertEqual(max_deposited, 183)
        self.assertEqual(deposited, 184)

    def test_bob_lb_tokens_value(self):
        self.assertEqual(
            get_lb_tokens_value(
                self.contract.tokenPool,
                self.contract.xtzPool,
                self.contract.lqtTotal,
                100_000,
            ),
            189_829_072,
        )

    def test_clare_lb_tokens_value(self):   
        self.assertEqual(
            get_lb_tokens_value(
                self.contract.tokenPool,
                self.contract.xtzPool,
                self.contract.lqtTotal,
                250_000,
            ),
            437_171_979,
        )


class RealStorageXTZToTokenTestCase(TestCase):
    """
    Operation https://better-call.dev/mainnet/opg/opSWd3SVciSmnsbLuHx831DZnVj62JUMhrLcePyhAK4jnrq7EEG/contents
    """
    def setUp(self):
        self.contract = Contract(
            27_944_134_536,
            4_398_189_886_967,
            271_360_616,
        )

    def test_xtz_to_token(self):
        self.assertEqual(
            self.contract.xtz_to_token_result(7_714_686_192),
            48_832_205,
        )
        self.assertEqual(self.contract.tokenPool, 27_895_302_331)
        self.assertEqual(self.contract.xtzPool, 4_405_896_858_472)


class RealStorageAddLiquidityTestCase(TestCase):
    """
    Operation https://better-call.dev/mainnet/opg/ooFroPPauHTzxhVuCUs2xb2PXLgHoThUmpaYohyepWKAQdu4bdN/contents
    """
    def setUp(self):
        self.contract = Contract(
            28_101_521_365,
            4_373_254_525_344,
            271_360_585,
        )

    def test_add_liquidity(self):
        self.assertEqual(
            self.contract.add_liquidity_result(500_000),
            3213,
        )
        self.assertEqual(self.contract.tokenPool, 28_101_524_578)
        self.assertEqual(self.contract.xtzPool, 4_373_255_025_344)
        self.assertEqual(self.contract.lqtTotal, 271_360_616)


class RealStorageTokenToXtzTestCase(TestCase):
    """
    Operation https://better-call.dev/mainnet/opg/op8dJdJFZdD6AHgZSQCKwUeoojkrvuXyky6sGx7xHXR9o7nNDdF/contents
    """
    def setUp(self):
        self.contract = Contract(
            30_038_448_280,
            4613771061436,
            284626110,
        )

    def test_add_liquidity(self):
        self.assertEqual(
            self.contract.token_to_xtz_result(31_639),
            4_849_888,
        )
        self.assertEqual(self.contract.tokenPool, 30_038_479_919)
        self.assertEqual(self.contract.xtzPool, 4613766206693)
        self.assertEqual(self.contract.lqtTotal, 284626110)

# TODO: find removeLiquidity operation

class RealStorageRemoveLiquidityTestCase(TestCase):
    def setUp(self):
        self.contract = Contract(
            28_101_521_365,
            4_373_254_525_344,
            271_360_585,
        )

    def test_add_liquidity(self):
        self.assertEqual(
            self.contract.remove_liquidity_result(1),
            (103, 16_116),
        )
        self.assertEqual(self.contract.tokenPool, 28_101_521_262)
        self.assertEqual(self.contract.xtzPool, 4_373_254_509_228)
        self.assertEqual(self.contract.lqtTotal, 271_360_584)

        self.assertEqual(
            self.contract.remove_liquidity_result(2),
            (207, 32_232),
        )
        self.assertEqual(self.contract.tokenPool, 28_101_521_055)
        self.assertEqual(self.contract.xtzPool, 4_373_254_476_996)
        self.assertEqual(self.contract.lqtTotal, 271_360_582)
