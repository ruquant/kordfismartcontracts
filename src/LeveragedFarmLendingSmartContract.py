import smartpy as sp
import os
import pathlib

ADMIN_ADDRESS = os.environ.get('ADMIN_ADDRESS', 'tz1VGzxpbAcP1CL5z8f8CZNGALFtMFCcakrX')
LIQUIDITY_BAKING_ADDRESS = os.environ.get('LIQUIDITY_BAKING_ADDRESS', 'tz1VGzxpbAcP1CL5z8f8CZNGALFtMFCcakrX')
FA_TZBTC_ADDRESS = os.environ.get('FA_TZBTC_ADDRESS', 'tz1VGzxpbAcP1CL5z8f8CZNGALFtMFCcakrX')
FA_LB_TOKEN_ADDRESS = os.environ.get('FA_LB_TOKEN_ADDRESS', 'tz1VGzxpbAcP1CL5z8f8CZNGALFtMFCcakrX')
ORACLE_ADDRESS = os.environ.get('ORACLE_ADDRESS', 'KT1P8Ep9y8EsDSD9YkvakWnDvF2orDcpYXSq')

FIXED_POINT_PRECISION = 12  # must be greater than 6
FIXED_POINT_FACTOR = 10 ** FIXED_POINT_PRECISION
MUTEZ_FIXED_POINT_FACTOR = 10 ** (FIXED_POINT_PRECISION - 6)
INITIAL_INDEX_VALUE = sp.nat(FIXED_POINT_FACTOR)

SPREAD_RATE = 128  # 0.4% annual rate
DEFAULT_RATE_1 = 3022  # 10% annual rate
DEFAULT_RATE_2 = 12857  # 50% annual rate
MAX_RATE_2 = 12857  # 50% annual rate
DEFAULT_TRESHOLD_PERCENT_1 = 80
DEFAULT_TRESHOLD_PERCENT_2 = 90

INFINITY_NAT = sp.nat(int(10**18))


def call_self_entry(entry_point):
    sp.transfer(sp.unit, sp.mutez(0), sp.self_entry_point(entry_point = entry_point))


def convert_mutez_to_nat(mutez_value):
    return sp.utils.mutez_to_nat(mutez_value) * sp.nat(MUTEZ_FIXED_POINT_FACTOR)


def convert_nat_to_mutez(nat_value):
    return sp.utils.nat_to_mutez(nat_value / sp.nat(MUTEZ_FIXED_POINT_FACTOR))


def ceildiv(numerator, denominator):
    return abs(sp.fst(sp.ediv(-numerator, denominator).open_some()))


def ceil_convert_nat_to_mutez(nat_value):
    return sp.utils.nat_to_mutez(ceildiv(nat_value, sp.nat(MUTEZ_FIXED_POINT_FACTOR)))


FA12 = sp.io.import_script_from_url(f'file://{pathlib.Path().resolve()}/src/FA1.2.py')

class LeveragedFarmLendingSmartContract(FA12.FA12_administrator,
                                        FA12.FA12_token_metadata,
                                        FA12.FA12_contract_metadata,
                                        FA12.FA12_core):
    def __init__(self, administrator, liquidity_baking_address, fa_tzBTC_address, fa_lb_address, oracle_address):
        config = FA12.FA12_config(support_upgradable_metadata = True, use_token_metadata_offchain_view = False)
        token_metadata = {
            'name': 'Kord.Fi tez deposit',
            'symbol': 'dtez',
            'decimals': '12',
            'thumbnailUri': 'https://ipfs.io/ipfs/QmP9ZXExg9EXXFtn8uLzyqMxecWVxUDb25reBCCoCzDPdt',
        }
        contract_metadata = {
            'name': 'XTZ Levered Farming Contract',
        }
        super().__init__(
            config,
            administrator = administrator,
            liquidity_baking_address = liquidity_baking_address,
            dex_contract_address = liquidity_baking_address,
            fa_tzBTC_address = fa_tzBTC_address,
            fa_lb_address = fa_lb_address,
            oracle_address = oracle_address,

            index_update_dttm = sp.now,
            gross_credit_index = INITIAL_INDEX_VALUE,
            deposit_index = INITIAL_INDEX_VALUE,
            net_credit_index = INITIAL_INDEX_VALUE,
            rate_params = sp.record(
                rate_1 = sp.nat(DEFAULT_RATE_1),
                rate_diff = sp.nat(DEFAULT_RATE_2 - DEFAULT_RATE_1),
                threshold_percent_1 = sp.nat(DEFAULT_TRESHOLD_PERCENT_1),
                threshold_percent_2 = sp.nat(DEFAULT_TRESHOLD_PERCENT_2),
            ),
            upfront_commission = sp.nat(1_000),  # 1%
            is_working = True,
            lb_price = sp.nat(1_000_000_000_000),
            lb_price_change_rate = sp.nat(5_787_000),  # ~ 50% per day

            onchain_liquidation_available = True,
            onchain_liquidation_percent = sp.nat(120),  # 120%
            onchain_liquidation_comm = sp.nat(50),  # 50%
            liquidation_percent = sp.nat(120),
            liquidation_price_percent = sp.nat(110),
            liquidation_comm = sp.nat(50),

            max_leverage = sp.nat(40),  # max leverage 4

            total_gross_credit = sp.nat(0),
            total_net_credit = sp.nat(0),

            lb_shares = sp.nat(0),
            index_delta = sp.nat(0),

            liquidity_book = sp.big_map(tkey=sp.TAddress, tvalue = sp.TRecord(
                net_credit = sp.TNat,  # loaned amount reduced with `net_credit_index` to contract start time
                gross_credit = sp.TNat,  # loaned amount reduced with `gross_credit_index` to contract start time
                lb_shares = sp.TNat,
            )),

            local_params = sp.record(
                fa_tzBTC_callback_status = sp.bool(False),
                fa_lb_callback_status = sp.bool(False),
                tzbtc_pool = sp.nat(0),
                lqt_total = sp.nat(0),
            ),

            flashloan_available = sp.bool(False),
            flashloan_admin_commission = sp.nat(100),  # 0.1%
            flashloan_deposit_commission = sp.nat(50),  # 0.05%
            flashloan_amount = sp.mutez(0),
        )
        self.set_token_metadata(token_metadata)
        self.set_contract_metadata(contract_metadata)


    @sp.entry_point
    def default(self):
        with sp.if_((sp.sender != self.data.liquidity_baking_address) & (sp.sender != self.data.dex_contract_address) & (self.data.totalSupply > sp.nat(0))):
            self.update_rates()
            self.data.deposit_index += convert_mutez_to_nat(sp.amount) * FIXED_POINT_FACTOR / self.data.totalSupply

    # @@ CPMM ProxyMethods
    def add_liquidity(self, amount, owner, minLqtMinted, maxTokensDeposited, deadline):
        handle = sp.contract(
            sp.TRecord(
                owner = sp.TAddress,
                minLqtMinted = sp.TNat,
                maxTokensDeposited = sp.TNat,
                deadline = sp.TTimestamp,
            ).layout(('owner', ('minLqtMinted', ('maxTokensDeposited', 'deadline')))),
            self.data.liquidity_baking_address,
            entry_point = 'addLiquidity'
        ).open_some('cant call addLiquidity')

        params = sp.record(
            owner = owner,
            minLqtMinted = minLqtMinted,
            maxTokensDeposited = maxTokensDeposited,
            deadline = deadline,
        )

        sp.transfer(params, amount, handle)

    def remove_liquidity(self, to, lqtBurned, minXtzWithdrawn, minTokensWithdrawn, deadline):
        handle = sp.contract(
            sp.TRecord(
                to = sp.TAddress,
                lqtBurned = sp.TNat,
                minXtzWithdrawn = sp.TMutez,
                minTokensWithdrawn = sp.TNat,
                deadline = sp.TTimestamp,
            ).layout(('to', ('lqtBurned', ('minXtzWithdrawn', ('minTokensWithdrawn', 'deadline'))))),
            self.data.liquidity_baking_address,
            entry_point = 'removeLiquidity'
        ).open_some('cant call removeLiquidity')

        params = sp.record(
            to = to,
            lqtBurned = lqtBurned,
            minXtzWithdrawn = minXtzWithdrawn,
            minTokensWithdrawn = minTokensWithdrawn,
            deadline = deadline,
        )

        sp.transfer(params, sp.mutez(0), handle)

    def token_to_xtz(self, to, tokensSold, minXtzBought, deadline):
        handle = sp.contract(
            sp.TRecord(
                to = sp.TAddress,
                tokensSold = sp.TNat,
                minXtzBought = sp.TMutez,
                deadline = sp.TTimestamp,
            ).layout(('to', ('tokensSold', ('minXtzBought', 'deadline')))),
            self.data.dex_contract_address,
            entry_point = 'tokenToXtz'
        ).open_some('cant call tokenToXtz')

        params = sp.record(
            to = to,
            tokensSold = tokensSold,
            minXtzBought = minXtzBought,
            deadline = deadline,
        )

        sp.transfer(params, sp.mutez(0), handle)

    def xtz_to_token(self, amount, to, minTokensBought, deadline):
        handle = sp.contract(
            sp.TRecord(
                to = sp.TAddress,
                minTokensBought = sp.TNat,
                deadline = sp.TTimestamp,
            ).layout(('to', ('minTokensBought', 'deadline'))),
            self.data.dex_contract_address,
            entry_point = 'xtzToToken'
        ).open_some('cant call xtzToToken')

        params = sp.record(
            to = to,
            minTokensBought = minTokensBought,
            deadline = deadline,
        )

        sp.transfer(params, amount, handle)

    def approve_lb_shares(self, spender, value):
        handle = sp.contract(
            sp.TRecord(
                spender = sp.TAddress,
                value = sp.TNat,
            ).layout(('spender', 'value')),
            self.data.fa_lb_address,
            entry_point = 'approve'
        ).open_some('cant call approve for LB shares')

        params = sp.record(
            spender = spender,
            value = value,
        )

        sp.transfer(params, sp.mutez(0), handle)

    def approve_tzBTC_shares(self, spender, value):
        handle = sp.contract(
            sp.TRecord(
                spender = sp.TAddress,
                value = sp.TNat,
            ).layout(('spender', 'value')),
            self.data.fa_tzBTC_address,
            entry_point = 'approve'
        ).open_some('cant call approve for tzBTC shares')

        params = sp.record(
            spender = spender,
            value = value,
        )

        sp.transfer(params, sp.mutez(0), handle)

    def transfer_tzBTC_shares(self, address_from, address_to, value):
        handle = sp.contract(
            sp.TRecord(**{
                'from': sp.TAddress,
                'to': sp.TAddress,
                'value': sp.TNat,
            }).layout(('from', ('to', 'value'))),
            self.data.fa_tzBTC_address,
            entry_point = 'transfer'
        ).open_some('cant call transfer for tzBTC shares')

        params = sp.record(**{
            'from': address_from,
            'to': address_to,
            'value': value,
        })

        sp.transfer(params, sp.mutez(0), handle)

    def transfer_LB_shares(self, address_from, address_to, value):
        handle = sp.contract(
            sp.TRecord(**{
                'from': sp.TAddress,
                'to': sp.TAddress,
                'value': sp.TNat,
            }).layout(('from', ('to', 'value'))),
            self.data.fa_lb_address,
            entry_point = 'transfer'
        ).open_some('cant call transfer for LB shares')

        params = sp.record(**{
            'from': address_from,
            'to': address_to,
            'value': value,
        })

        sp.transfer(params, sp.mutez(0), handle)

    # @@ Indexes part
    @sp.entry_point
    def setIsWorkingStatus(self, value):
        sp.set_type(value, sp.TBool)
        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        self.update_rates()
        self.data.is_working = value

    @sp.entry_point
    def disableOnchainLiquidation(self):
        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        self.data.onchain_liquidation_available = False

    @sp.entry_point
    def setUpfrontCommission(self, value):
        sp.set_type(value, sp.TNat)
        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        sp.verify(value <= 2_000, 'upfront commission max value error')
        self.data.upfront_commission = value

    @sp.entry_point
    def setLbPriceChangeRate(self, value):
        sp.set_type(value, sp.TNat)
        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        sp.verify(value <= 277_777_777, 'price change rate max value error') # 50% per hour
        self.data.lb_price_change_rate = value

    def update_lb_shares(self):
        self.data.local_params.fa_lb_callback_status = sp.bool(True)

        handle = sp.contract(
            sp.TRecord(
                owner = sp.TAddress,
                callback = sp.TContract(sp.TNat),
            ).layout(('owner', 'callback')), 
            self.data.fa_lb_address, 
            entry_point = "getBalance",
        ).open_some('cant call getBalance for LB shares')

        params = sp.record(
            owner = sp.self_address,
            callback = sp.self_entry_point(entry_point = 'updateLBCallback'),
        )

        sp.transfer(params, sp.mutez(0), handle)

    @sp.entry_point
    def updateLBCallback(self, lb_shares):
        sp.set_type(lb_shares, sp.TNat)
        sp.verify(self.data.fa_lb_address == sp.sender, 'Forbidden.')
        sp.verify(self.data.local_params.fa_lb_callback_status, 'Bad status.')
        self.data.local_params.fa_lb_callback_status = sp.bool(False)
        self.data.lb_shares = lb_shares

    def updateTzbtcPool(self):
        handle = sp.contract(
            sp.TRecord(
                owner = sp.TAddress,
                callback = sp.TContract(sp.TNat),
            ).layout(('owner', 'callback')),
            self.data.fa_tzBTC_address, 
            entry_point = "getBalance",
        ).open_some('cant call getBalance for tzBTC')

        params = sp.record(
            owner = self.data.liquidity_baking_address,
            callback = sp.self_entry_point(entry_point = 'updateTzbtcPoolCallback'),
        )

        sp.transfer(params, sp.mutez(0), handle)

    @sp.entry_point
    def updateTzbtcPoolCallback(self, tzbtc_pool):
        sp.set_type(tzbtc_pool, sp.TNat)
        sp.verify(self.data.fa_tzBTC_address == sp.sender, 'Forbidden.')
        self.data.local_params.tzbtc_pool = tzbtc_pool

    def updateLqtTotal(self):
        handle = sp.contract(
            sp.TRecord(
                request = sp.TUnit,
                callback = sp.TContract(sp.TNat),
            ).layout(('request', 'callback')),
            self.data.fa_lb_address, 
            entry_point = "getTotalSupply",
        ).open_some('cant call getTotalSupply of lb token')

        params = sp.record(
            request = sp.unit,
            callback = sp.self_entry_point(entry_point = 'updateLqtTotalCallback'),
        )

        sp.transfer(params, sp.mutez(0), handle)

    @sp.entry_point
    def updateLqtTotalCallback(self, lqt_total):
        sp.set_type(lqt_total, sp.TNat)
        sp.verify(self.data.fa_lb_address == sp.sender, 'Forbidden.')
        self.data.local_params.lqt_total = lqt_total

    @sp.entry_point
    def setDelegate(self, delegate):
        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        sp.set_delegate(delegate)

    @sp.entry_point
    def withdrawCommission(self):
        self.update_rates()

        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        delta = sp.local(
            'delta',
            (   
                convert_mutez_to_nat(sp.balance) * INITIAL_INDEX_VALUE
                +
                self.data.total_gross_credit * self.data.gross_credit_index
                -
                self.data.totalSupply * self.data.deposit_index
            )
        )
        with sp.if_(delta.value > 0):
            mutez_delta = sp.local('mutez_delta', convert_nat_to_mutez(sp.as_nat(delta.value) / INITIAL_INDEX_VALUE))
            with sp.if_(mutez_delta.value > sp.mutez(0)):
                with sp.if_(mutez_delta.value < sp.balance):
                    sp.send(self.data.administrator, mutez_delta.value)
                with sp.else_():
                    sp.send(self.data.administrator, sp.balance)

    @sp.entry_point
    def setDexContract(self, address):
        sp.set_type(address, sp.TAddress)
        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        self.data.dex_contract_address = address

    @sp.entry_point
    def setRateParams(self, params):
        """
        @params fields:
            rate_1 - RATE_1 rate param
            rate_diff - (RATE_2 - RATE_1) diff rate param
            threshold_percent_1 - the first threshold percent
            threshold_percent_2 - the second threshold percent
        """
        sp.set_type(params,
            sp.TRecord(rate_1=sp.TNat, rate_diff=sp.TNat, threshold_percent_1=sp.TNat, threshold_percent_2=sp.TNat).
            layout(("rate_1", ("rate_diff", ("threshold_percent_1", "threshold_percent_2"))))
        )

        rate_1 = params.rate_1
        rate_diff = params.rate_diff
        threshold_percent_1 = params.threshold_percent_1
        threshold_percent_2 = params.threshold_percent_2

        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        self.update_rates()

        sp.verify(rate_1 + rate_diff <= sp.nat(MAX_RATE_2), 'rate2 max value error')
        sp.verify(threshold_percent_2 <= 100, 'wrong threshold percent')
        sp.verify(threshold_percent_1 <= threshold_percent_2, 'wrong threshold percent')

        self.data.rate_params.rate_1 = rate_1
        self.data.rate_params.rate_diff = rate_diff
        self.data.rate_params.threshold_percent_1 = threshold_percent_1
        self.data.rate_params.threshold_percent_2 = threshold_percent_2

    @sp.entry_point
    def setLeverageParams(self, params):
        """
        @params fields:
            max_leverage - Max amount of leverage available for an additional farm investment
            onchain_liquidation_percent - Collateral ratio threshold, under which the farm is open to liquidation by admin with onchain liquidation
            onchain_liquidation_comm - Share of the liquidation reward that is paid to admin with onchain liquidation
            liquidation_percent - Collateral ratio threshold, under which the farm is open to common liquidation
            liquidation_price_percent - Collateral ratio threshold, that should be paid to liquidate the farm
            liquidation_comm - Share of the liquidation reward that is paid to admin with common liquidation
            oracle_address - BTC and xtz price oracle
        """
        sp.set_type(params,
            sp.TRecord(
                max_leverage=sp.TNat,
                onchain_liquidation_percent=sp.TNat,
                onchain_liquidation_comm=sp.TNat,
                liquidation_percent = sp.TNat,
                liquidation_price_percent = sp.TNat,
                liquidation_comm = sp.TNat,
                oracle_address = sp.TAddress,
            ).layout((
                "max_leverage", (
                    "onchain_liquidation_percent", (
                        "onchain_liquidation_comm", (
                            "liquidation_percent", (
                                "liquidation_price_percent", (
                                    "liquidation_comm",
                                    "oracle_address",
                                ),
                            ),
                        ),
                    ),
                ),
            ))
        )

        max_leverage = params.max_leverage
        onchain_liquidation_percent = params.onchain_liquidation_percent
        onchain_liquidation_comm = params.onchain_liquidation_comm
        liquidation_percent = params.liquidation_percent
        liquidation_price_percent = params.liquidation_price_percent
        liquidation_comm = params.liquidation_comm
        oracle_address = params.oracle_address

        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')

        sp.verify(max_leverage >= sp.nat(20), 'max_leverage min value error')
        sp.verify(max_leverage <= sp.nat(100), 'max_leverage max value error')

        sp.verify(onchain_liquidation_percent > sp.nat(100), 'onchain_liquidation_percent min value error')
        sp.verify(onchain_liquidation_percent <= sp.nat(200), 'onchain_liquidation_percent max value error')

        sp.verify(onchain_liquidation_comm <= sp.nat(100), 'onchain_liquidation_comm max value error')

        sp.verify(liquidation_percent > sp.nat(100), 'liquidation_percent min value error')
        sp.verify(liquidation_percent <= sp.nat(200), 'liquidation_percent max value error')

        sp.verify(liquidation_price_percent > sp.nat(100), 'liquidation_price_percent min value error')
        sp.verify(liquidation_price_percent <= liquidation_percent, 'liquidation_percent max value error')

        sp.verify(liquidation_comm <= sp.nat(100), 'liquidation_comm max value error')

        self.data.max_leverage = max_leverage
        self.data.onchain_liquidation_percent = onchain_liquidation_percent
        self.data.onchain_liquidation_comm = onchain_liquidation_comm
        self.data.liquidation_percent = liquidation_percent
        self.data.liquidation_price_percent = liquidation_price_percent
        self.data.liquidation_comm = liquidation_comm
        self.data.oracle_address = oracle_address

    def get_gross_credit_rate(self):
        adjusted_utilization = sp.local('adjusted_utilization', sp.nat(0))
        with sp.if_(self.data.totalSupply > sp.nat(0)):
            adjusted_utilization.value = (
                self.data.total_gross_credit * self.data.gross_credit_index * FIXED_POINT_FACTOR 
                / 
                (self.data.totalSupply * self.data.deposit_index)
            )

        rate = sp.local('rate', sp.nat(0))

        rate_1 = self.data.rate_params.rate_1
        rate_diff = self.data.rate_params.rate_diff
        threshold_percent_1 = sp.local('threshold_percent_1', self.data.rate_params.threshold_percent_1 * 10 ** (FIXED_POINT_PRECISION - 2))
        threshold_percent_2 = sp.local('threshold_percent_2', self.data.rate_params.threshold_percent_2 * 10 ** (FIXED_POINT_PRECISION - 2))

        with sp.if_(adjusted_utilization.value < threshold_percent_1.value):
            rate.value = rate_1 * adjusted_utilization.value / threshold_percent_1.value

        with sp.else_():
            with sp.if_(adjusted_utilization.value < threshold_percent_2.value):
                rate.value = rate_1

            with sp.else_():

                with sp.if_(adjusted_utilization.value < FIXED_POINT_FACTOR):
                    rate.value = (
                        rate_1
                        +
                        rate_diff * sp.as_nat(adjusted_utilization.value - threshold_percent_2.value)
                        /
                        sp.as_nat(FIXED_POINT_FACTOR - threshold_percent_2.value)
                    )
                with sp.else_():
                    rate.value = rate_1 + rate_diff

        return rate.value

    def update_rates(self):
        with sp.if_(self.data.index_update_dttm != sp.now):
            self.update_rates_lambda()
            self.update_lb_price()

    @sp.private_lambda(with_storage='read-write', with_operations=True, wrap_call=True)
    def update_rates_lambda(self):
        dttm_delta = sp.local('dttm_delta', sp.as_nat(sp.now - self.data.index_update_dttm))

        utilization = sp.local('utilization', sp.nat(0))
        with sp.if_(self.data.totalSupply > sp.nat(0)):
            utilization.value = (
                self.data.total_net_credit * self.data.net_credit_index * FIXED_POINT_FACTOR 
                / 
                (self.data.totalSupply * self.data.deposit_index)
            )

        gross_credit_rate = self.get_gross_credit_rate()
        self.data.gross_credit_index = ceildiv(self.data.gross_credit_index * (FIXED_POINT_FACTOR + gross_credit_rate * dttm_delta.value), FIXED_POINT_FACTOR)

        net_credit_rate = sp.local('net_credit_rate', sp.nat(0))
        with sp.if_(self.data.is_working):
            net_credit_rate.value = gross_credit_rate * 9 / 10  # 90% commission factor
        self.data.net_credit_index = ceildiv(self.data.net_credit_index * (FIXED_POINT_FACTOR + net_credit_rate.value * dttm_delta.value), FIXED_POINT_FACTOR)

        deposit_rate = sp.local('deposit_rate', net_credit_rate.value * utilization.value / FIXED_POINT_FACTOR)
        self.data.deposit_index = self.data.deposit_index * (FIXED_POINT_FACTOR + deposit_rate.value * dttm_delta.value) / FIXED_POINT_FACTOR

    def update_lb_price(self):
        # update external parameters, call calculateLbPrice
        self.updateLqtTotal()
        self.updateTzbtcPool()
        sp.transfer(
            arg = sp.unit,
            amount = sp.mutez(0),
            destination = sp.self_entry_point(entry_point = "calculateLbPrice"),
        )

    @sp.entry_point
    def calculateLbPrice(self):
        sp.verify(sp.self_address == sp.sender, 'Forbidden.')

        with sp.if_(self.data.local_params.lqt_total > 0):
            # new_lb_price = clamp(calculated_lb_price, lb_price * (1 - e * dt), lb_price * (1 + e * dt))
            calculated_lb_price = sp.local('calculated_lb_price',
                self.data.local_params.tzbtc_pool * FIXED_POINT_FACTOR / self.data.local_params.lqt_total)
            with sp.if_(calculated_lb_price.value > self.data.lb_price):
                self.data.lb_price = sp.min(
                    calculated_lb_price.value,
                    self.data.lb_price * (FIXED_POINT_FACTOR + self.data.lb_price_change_rate * sp.as_nat(sp.now - self.data.index_update_dttm)) / FIXED_POINT_FACTOR,
                )
            with sp.else_():
                self.data.lb_price = sp.max(
                    calculated_lb_price.value,
                    self.data.lb_price * sp.as_nat(
                        sp.max(1, FIXED_POINT_FACTOR - self.data.lb_price_change_rate * sp.as_nat(sp.now - self.data.index_update_dttm))
                    ) / FIXED_POINT_FACTOR,
                )

        self.data.index_update_dttm = sp.now

    @sp.private_lambda(with_storage='read-only', with_operations=False, wrap_call=True)
    def check_totalSupply_net_credit_inequation(self):
        sp.verify(
            self.data.totalSupply * self.data.deposit_index >= self.data.total_net_credit * self.data.net_credit_index,
            'total deposit and net credit inequation error'
        )

    @sp.entry_point
    def updateIndexes(self):
        self.update_rates()

    # @@ Lending part
    @sp.entry_point
    def depositLending(self):
        self.update_rates()

        self.addAddressIfNecessary(sp.sender)
        deposit_amount = sp.local('deposit_amount', convert_mutez_to_nat(sp.amount) * INITIAL_INDEX_VALUE / self.data.deposit_index)
        self.data.ledger[sp.sender].balance += deposit_amount.value
        self.data.totalSupply += deposit_amount.value

    @sp.entry_point
    def redeemLending(self, amount):
        sp.set_type(amount, sp.TMutez)

        sp.verify(sp.amount == sp.mutez(0), 'Amount is not allowed.')
        sp.verify(self.data.ledger.contains(sp.sender), 'Unknown Address.')
        sp.verify(sp.balance >= amount, 'Not enough balance')

        self.update_rates()

        redeem_deposit = sp.local('redeem_deposit', ceildiv(convert_mutez_to_nat(amount) * INITIAL_INDEX_VALUE, self.data.deposit_index))
        self.data.ledger[sp.sender].balance = sp.as_nat(
            self.data.ledger[sp.sender].balance - redeem_deposit.value,
            message = 'too much amount'
        )
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - redeem_deposit.value, message='wrong total deposit value')
        sp.send(sp.sender, amount)

        self.check_totalSupply_net_credit_inequation()

    # @@ Farm part
    def call_sellTzBTC(self):
        self.data.local_params.fa_tzBTC_callback_status = sp.bool(True)

        handle = sp.contract(
            sp.TRecord(
                owner = sp.TAddress,
                callback = sp.TContract(sp.TNat),
            ).layout(('owner', 'callback')),
            self.data.fa_tzBTC_address,
            entry_point = "getBalance",
        ).open_some('cant call getBalance for tzBTC shares')

        params = sp.record(
            owner = sp.self_address,
            callback = sp.self_entry_point(entry_point = 'sellTzBTC'),
        )

        sp.transfer(params, sp.mutez(0), handle)

    @sp.entry_point
    def sellTzBTC(self, tzBTC_shares):
        sp.set_type(tzBTC_shares, sp.TNat)
        sp.verify(self.data.fa_tzBTC_address == sp.sender, 'Forbidden.')
        sp.verify(self.data.local_params.fa_tzBTC_callback_status, 'Bad status.')
        self.data.local_params.fa_tzBTC_callback_status = sp.bool(False)

        with sp.if_(tzBTC_shares > sp.nat(0)):
            self.approve_tzBTC_shares(
                spender = self.data.dex_contract_address,
                value = INFINITY_NAT,
            )

            self.token_to_xtz(
                to = sp.self_address,
                tokensSold = tzBTC_shares,
                minXtzBought = sp.mutez(0),
                deadline = sp.now.add_seconds(1),
            )

            self.approve_tzBTC_shares(
                spender = self.data.dex_contract_address,
                value = sp.nat(0),
            )

    def sell_LB(self, shares, minTokensWithdrawn):
        self.data.lb_shares = sp.as_nat(self.data.lb_shares - shares)

        self.approve_lb_shares(
            spender = self.data.liquidity_baking_address,
            value = shares,
        )

        self.remove_liquidity(
            to = sp.self_address,
            lqtBurned = shares,
            minXtzWithdrawn = sp.mutez(0),
            minTokensWithdrawn = minTokensWithdrawn,
            deadline = sp.now.add_seconds(1),
        )

        self.approve_lb_shares(
            spender = self.data.liquidity_baking_address,
            value = sp.nat(0),
        )

    def reset_liquidity_entry(self, address):
        sp.set_type(address, sp.TAddress)

        debt_amount = sp.local('debt_amount', 
            ceil_convert_nat_to_mutez(ceildiv(self.data.liquidity_book[address].gross_credit * self.data.gross_credit_index, INITIAL_INDEX_VALUE)))

        self.data.total_net_credit = sp.as_nat(self.data.total_net_credit - self.data.liquidity_book[address].net_credit)
        self.data.total_gross_credit = sp.as_nat(self.data.total_gross_credit - self.data.liquidity_book[address].gross_credit)

        self.data.liquidity_book[address].lb_shares = sp.nat(0)
        self.data.liquidity_book[address].net_credit = sp.nat(0)
        self.data.liquidity_book[address].gross_credit = sp.nat(0)

        return debt_amount

    def partial_reset_liquidity_entry(self, address, lqtBurned):
        sp.set_type(address, sp.TAddress)
        sp.set_type(lqtBurned, sp.TNat)

        total_lb_shares = sp.local('total_lb_shares', self.data.liquidity_book[address].lb_shares)

        debt_amount = sp.local('debt_amount', ceil_convert_nat_to_mutez(
            ceildiv(self.data.liquidity_book[address].gross_credit * self.data.gross_credit_index * lqtBurned, INITIAL_INDEX_VALUE * total_lb_shares.value))
        )

        liquidated_gross_credit = sp.local('liquidated_gross_credit', self.data.liquidity_book[address].gross_credit * lqtBurned / total_lb_shares.value)
        self.data.total_gross_credit = sp.as_nat(self.data.total_gross_credit - liquidated_gross_credit.value)
        self.data.liquidity_book[address].gross_credit = sp.as_nat(
            self.data.liquidity_book[address].gross_credit - liquidated_gross_credit.value,
            message='wrong liquidated gross credit',
        )

        liquidated_net_credit = sp.local('liquidated_net_credit', self.data.liquidity_book[address].net_credit * lqtBurned / total_lb_shares.value)
        self.data.total_net_credit = sp.as_nat(self.data.total_net_credit - liquidated_net_credit.value)
        self.data.liquidity_book[address].net_credit = sp.as_nat(
            self.data.liquidity_book[address].net_credit - liquidated_net_credit.value,
            message='wrong liquidated net credit',
        )

        self.data.liquidity_book[address].lb_shares = sp.as_nat(
            total_lb_shares.value - lqtBurned,
            message='wrong liquidated shares',
        )

        return debt_amount

    @sp.entry_point
    def investLB(self, params):
        """
        @params fields:
            amount2tzBTC - xtz amount converted to tzBTC
            mintzBTCTokensBought - minimum tzBTC to buy
            amount2Lqt - xtz amount converted to LB tokens
            minLqtMinted - minimum LB tokens to mint
            tzBTCShares - tzBTC shares provided by client
        """
        sp.set_type(params,
            sp.TRecord(amount2tzBTC=sp.TMutez, mintzBTCTokensBought=sp.TNat, amount2Lqt=sp.TMutez, minLqtMinted=sp.TNat, tzBTCShares=sp.TNat).
            layout(("amount2tzBTC", ("mintzBTCTokensBought", ("amount2Lqt", ("minLqtMinted", "tzBTCShares")))))
        )

        amount2tzBTC = params.amount2tzBTC
        mintzBTCTokensBought = params.mintzBTCTokensBought
        amount2Lqt = params.amount2Lqt
        minLqtMinted = params.minLqtMinted
        tzBTCShares = params.tzBTCShares

        self.update_rates()

        # upfront_commission
        upfront_commission = sp.local(
            'upfront_commission',
            sp.split_tokens(
                amount2Lqt + amount2tzBTC - sp.amount, 
                self.data.upfront_commission, 
                sp.as_nat(100000 - self.data.upfront_commission),
            )
        )
        with sp.if_(upfront_commission.value > sp.mutez(0)):
            sp.send(self.data.administrator, upfront_commission.value)

        # amount2Lqt + amount2tzBTC <= max_leverage * (sent_amount - upfront_commission)
        # we doesnt count value tzBTCShares in collateral
        sp.verify(
            sp.mul(amount2Lqt + amount2tzBTC, sp.nat(10)) <= sp.mul(sp.amount - upfront_commission.value, self.data.max_leverage),
            'leverage error'
        )

        with sp.if_(tzBTCShares > sp.nat(0)):
            self.transfer_tzBTC_shares(
                address_from = sp.sender,
                address_to = sp.self_address, 
                value = tzBTCShares,
            )

        with sp.if_(amount2tzBTC > sp.mutez(0)):
            self.xtz_to_token(
                amount = amount2tzBTC,
                to = sp.self_address,
                minTokensBought = mintzBTCTokensBought,
                deadline = sp.now.add_seconds(1),
            )

        self.approve_tzBTC_shares(
            spender = self.data.liquidity_baking_address,
            value = INFINITY_NAT,
        )

        self.add_liquidity(
            amount = amount2Lqt,
            owner = sp.self_address,
            minLqtMinted = minLqtMinted,
            maxTokensDeposited = INFINITY_NAT,
            deadline = sp.now.add_seconds(1),
        )

        self.approve_tzBTC_shares(
            spender = self.data.liquidity_baking_address,
            value = sp.nat(0),
        )

        self.update_lb_shares()
        self.call_sellTzBTC()

        # call investLBFinalize
        sp.transfer(
            arg = sp.record(
                address = sp.sender,
                initial_balance = sp.sub_mutez(sp.balance, sp.amount).open_some(),
                initial_lb_shares = self.data.lb_shares,
            ), 
            amount = sp.mutez(0), 
            destination = sp.self_entry_point(entry_point = "investLBFinalize"),
        )

    @sp.entry_point
    def investLBFinalize(self, params):
        """
        @params fields:
            address - farmer address
            initial_balance - initial balance amount, before calling investLB entry
            initial_lb_shares - initial value if lb_shares, before calling investLB entry
        """
        sp.set_type(params,
            sp.TRecord(address=sp.TAddress, initial_balance=sp.TMutez, initial_lb_shares=sp.TNat).
            layout(("address", ("initial_balance", "initial_lb_shares")))
        )

        address = params.address
        initial_balance = params.initial_balance
        initial_lb_shares = params.initial_lb_shares

        sp.verify(sp.self_address == sp.sender, 'Forbidden.')

        with sp.if_(~self.data.liquidity_book.contains(address)):
            self.data.liquidity_book[address] = sp.record(
                lb_shares = sp.nat(0),
                net_credit = sp.nat(0),
                gross_credit = sp.nat(0),
            )

        balance_delta = sp.sub_mutez(initial_balance, sp.balance).open_some('negative balance delta error')
        a = sp.local('a', convert_mutez_to_nat(balance_delta) * INITIAL_INDEX_VALUE)

        additional_net_credit = sp.local('additional_net_credit', ceildiv(a.value, self.data.net_credit_index))
        self.data.liquidity_book[address].net_credit += additional_net_credit.value
        self.data.total_net_credit += additional_net_credit.value

        additional_gross_credit = sp.local('additional_gross_credit', ceildiv(a.value, self.data.gross_credit_index))
        self.data.liquidity_book[address].gross_credit += additional_gross_credit.value
        self.data.total_gross_credit += additional_gross_credit.value

        lb_delta = sp.local('lb_delta', sp.as_nat(self.data.lb_shares - initial_lb_shares, message='negative lb delta error'))
        self.data.liquidity_book[address].lb_shares += lb_delta.value

        self.check_totalSupply_net_credit_inequation()

    @sp.entry_point
    def redeemLB(self, params):
        """
        @params fields:
            lqtBurned - LB shares to burn
            minTokensWithdrawn - minimum tzBTC to buy
        """
        sp.set_type(params,
            sp.TRecord(lqtBurned=sp.TNat, minTokensWithdrawn=sp.TNat).
            layout(("lqtBurned", "minTokensWithdrawn"))
        )

        lqtBurned = params.lqtBurned
        minTokensWithdrawn = params.minTokensWithdrawn

        sp.verify(sp.amount == sp.mutez(0), 'Amount is not allowed.')

        self.update_rates()

        self.sell_LB(
            shares = lqtBurned,
            minTokensWithdrawn = minTokensWithdrawn,
        )

        self.call_sellTzBTC() 

        # call redeemLBFinalize
        sp.transfer(
            arg = sp.record(
                address = sp.sender,
                lqtBurned = lqtBurned,
                initial_balance = sp.balance,
            ), 
            amount = sp.mutez(0), 
            destination = sp.self_entry_point(entry_point = "redeemLBFinalize"),
        )

    @sp.entry_point
    def redeemLBFinalize(self, params):
        """
        @params fields:
            address - farmer address
            lqtBurned - LB shares to burn
            initial_balance - initial balance amount, before calling investLB entry
        """
        sp.set_type(params,
            sp.TRecord(address=sp.TAddress, lqtBurned=sp.TNat, initial_balance=sp.TMutez).
            layout(("address", ("lqtBurned", "initial_balance")))
        )

        address = params.address
        lqtBurned = params.lqtBurned
        initial_balance = params.initial_balance

        sp.verify(sp.self_address == sp.sender, 'Forbidden.')

        balance_delta = sp.local('balance_delta', sp.sub_mutez(sp.balance, initial_balance).open_some('negative balance delta error'))

        debt_amount = self.partial_reset_liquidity_entry(address, lqtBurned)

        sp.send(address, sp.sub_mutez(balance_delta.value, debt_amount.value).open_some())

    @sp.entry_point
    def liquidateLB(self, address):
        sp.set_type(address, sp.TAddress)
        self.update_rates()

        sp.verify(self.data.liquidity_book.contains(address), 'Unknown Address.')
        sp.verify(self.data.liquidity_book[address].net_credit > sp.nat(0), 'not loaned')

        # call liquidateLBFinalize
        sp.transfer(
            arg = sp.record(
                address = address,
                sender = sp.sender,
                sent_amount = sp.amount,
            ), 
            amount = sp.mutez(0), 
            destination = sp.self_entry_point(entry_point = "liquidateLBFinalize"),
        )

    @sp.entry_point
    def liquidateLBFinalize(self, params):
        """
        @params fields:
            address - farmer address
            sender - liquidator adress
            sent_amount - amount of xtz, sent by liquidator
        """
        sp.set_type(params,
            sp.TRecord(address=sp.TAddress, sender=sp.TAddress, sent_amount=sp.TMutez).
            layout(("address", ("sender", "sent_amount")))
        )

        sp.verify(sp.self_address == sp.sender, 'Forbidden.')
        address = params.address

        # xtzPool / tokenPool = tzbtc_price / (100 * xtz_price)
        tzbtc_price = sp.view("get_price", self.data.oracle_address, 'BTC', t=sp.TNat).open_some('invalid view')
        xtz_price = sp.view("get_price", self.data.oracle_address, 'XTZ', t=sp.TNat).open_some('invalid view')

        # verify liquidation percent and liquidation price
        lb_shares = sp.local('lb_shares', self.data.liquidity_book[params.address].lb_shares)
        tzbtc_pool = self.data.local_params.tzbtc_pool
        # *_value variables multiplied by 10^8
        lb_shares_value = lb_shares.value * 2 * self.data.lb_price * tzbtc_price / FIXED_POINT_FACTOR # / 10^8
        debt_amount = sp.local('debt_amount', 
            ceil_convert_nat_to_mutez(ceildiv(self.data.liquidity_book[params.address].gross_credit * self.data.gross_credit_index, INITIAL_INDEX_VALUE)))
        debt_value = xtz_price * sp.utils.mutez_to_nat(debt_amount.value) * 100 # / 10^8
        sent_amount_value = sp.utils.mutez_to_nat(params.sent_amount) * xtz_price * 100 # / 10^8
        sp.verify(lb_shares_value * 100 < debt_value * self.data.liquidation_percent, 'liquidation is not allowed')

        # liquidation
        liquidated_debt_amount = sp.split_tokens(params.sent_amount, 100, self.data.liquidation_price_percent)
        liquidated_gross_credit = sp.local('liquidated_gross_credit', sp.min(
            convert_mutez_to_nat(liquidated_debt_amount) * INITIAL_INDEX_VALUE / self.data.gross_credit_index,
            self.data.liquidity_book[address].gross_credit,
        ))
        liquidated_net_credit = sp.local('liquidated_net_credit', self.data.liquidity_book[address].net_credit * liquidated_gross_credit.value / self.data.liquidity_book[address].gross_credit)
        liquidated_lb_shares = sp.local('liquidated_lb_shares', lb_shares.value * liquidated_gross_credit.value / self.data.liquidity_book[address].gross_credit)

        self.data.total_net_credit = sp.as_nat(self.data.total_net_credit - liquidated_net_credit.value)
        self.data.total_gross_credit = sp.as_nat(self.data.total_gross_credit - liquidated_gross_credit.value)
        self.data.liquidity_book[address].gross_credit = sp.as_nat(
            self.data.liquidity_book[address].gross_credit - liquidated_gross_credit.value,
            message='wrong liquidated gross credit',
        )
        self.data.liquidity_book[address].net_credit = sp.as_nat(
            self.data.liquidity_book[address].net_credit - liquidated_net_credit.value,
            message='wrong liquidated net credit',
        )
        self.data.liquidity_book[address].lb_shares = sp.as_nat(
            lb_shares.value - liquidated_lb_shares.value,
            message='wrong liquidated shares',
        )

        # send values
        extra_supply = sp.local('extra_supply', sp.sub_mutez(params.sent_amount, liquidated_debt_amount).open_some('negative balance delta error'))
        admin_comm = sp.local('admin_comm', sp.split_tokens(extra_supply.value, self.data.liquidation_comm, 100))
        with sp.if_(admin_comm.value > sp.mutez(0)):
            sp.send(self.data.administrator, admin_comm.value)
        self.data.deposit_index += convert_mutez_to_nat(
            sp.sub_mutez(extra_supply.value, admin_comm.value).open_some('admin commission error')
        ) * FIXED_POINT_FACTOR / self.data.totalSupply
        self.transfer_LB_shares(sp.self_address, params.sender, liquidated_lb_shares.value)
        self.data.lb_shares = sp.as_nat(self.data.lb_shares - liquidated_lb_shares.value)

    @sp.entry_point
    def liquidateOnchainLB(self, address):
        sp.set_type(address, sp.TAddress)

        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')
        sp.verify(self.data.onchain_liquidation_available, 'Onchain liquidation disabled.')

        self.update_rates()

        sp.verify(self.data.liquidity_book.contains(address), 'Unknown Address.')
        sp.verify(self.data.liquidity_book[address].net_credit > sp.nat(0), 'not loaned')

        self.sell_LB(
            shares = self.data.liquidity_book[address].lb_shares,
            minTokensWithdrawn = sp.nat(0),
        )

        self.call_sellTzBTC()

        # call liquidateOnchainLBFinalize
        sp.transfer(
            arg = sp.record(
                address = address,
                initial_balance = sp.balance,
            ), 
            amount = sp.mutez(0), 
            destination = sp.self_entry_point(entry_point = "liquidateOnchainLBFinalize"),
        )

    @sp.entry_point
    def liquidateOnchainLBFinalize(self, params):
        """
        @params fields:
            address - farmer address
            initial_balance - initial balance amount, after calling liquidateLB entry
        """
        sp.set_type(params,
            sp.TRecord(address=sp.TAddress, initial_balance=sp.TMutez).
            layout(("address", "initial_balance"))
        )

        address = params.address
        initial_balance = params.initial_balance

        sp.verify(sp.self_address == sp.sender, 'Forbidden.')

        delta = sp.local('delta', sp.sub_mutez(sp.balance, initial_balance).open_some('negative balance delta error'))
        debt_amount = self.reset_liquidity_entry(address)

        sp.verify(sp.mul(delta.value, sp.nat(100)) < sp.mul(debt_amount.value, self.data.onchain_liquidation_percent), 'liquidation is not allowed')
 
        extra_supply = sp.local('extra_supply', convert_mutez_to_nat(delta.value) - convert_mutez_to_nat(debt_amount.value))
        with sp.if_(extra_supply.value > sp.int(0)):
            admin_comm = sp.local('admin_comm', convert_nat_to_mutez(sp.as_nat(extra_supply.value) * self.data.onchain_liquidation_comm / 100))
            with sp.if_(admin_comm.value > sp.mutez(0)):
                sp.send(self.data.administrator, admin_comm.value)
            self.data.deposit_index += sp.as_nat(sp.as_nat(extra_supply.value) - convert_mutez_to_nat(admin_comm.value)) * FIXED_POINT_FACTOR / self.data.totalSupply
            # totalSupply > 0 because if we have at least one active farm account: 0 < total_net_credit_now <= totalSupply_now
            # thats why we dont need check totalSupply != 0

        with sp.else_():
            self.data.deposit_index = sp.as_nat(self.data.deposit_index - ceildiv(sp.as_nat(-extra_supply.value) * FIXED_POINT_FACTOR, self.data.totalSupply))
            # the same above

    # @@ Flashloan part
    @sp.entry_point
    def setFlashloanParams(self, params):
        """
        @params fields:
            flashloan_admin_commission - Flashloan commission charged by contract owner.
            flashloan_deposit_commission - Flashloan commission allocated to Lenders.
            flashloan_available - Flag tells if flashloans are enabled or not. flashloan_available=true means flashloans are enabled.
        """
        sp.set_type(params,
            sp.TRecord(flashloan_admin_commission=sp.TNat, flashloan_deposit_commission=sp.TNat, flashloan_available=sp.TBool).
            layout(('flashloan_admin_commission', ('flashloan_deposit_commission', 'flashloan_available')))
        )
        
        sp.verify(self.data.administrator == sp.sender, 'Forbidden.')

        self.data.flashloan_admin_commission = params.flashloan_admin_commission
        self.data.flashloan_deposit_commission = params.flashloan_deposit_commission
        self.data.flashloan_available = params.flashloan_available

    @sp.entry_point
    def flashloan(self, params):
        """
        @params fields:
            callback - callback entry
            requested_xtz - requested flashloan amount
        """
        sp.set_type(params,
            sp.TRecord(callback=sp.TContract(sp.TUnit), requested_xtz=sp.TMutez).
            layout(('callback', 'requested_xtz'))
        )

        requested_xtz = params.requested_xtz

        sp.verify(self.data.flashloan_available, 'flashloan is not available')
        sp.verify(requested_xtz > sp.mutez(0), 'zero requested amount')

        self.update_rates()

        self.data.flashloan_amount += sp.utils.nat_to_mutez(
            ceildiv(sp.utils.mutez_to_nat(requested_xtz) * (sp.nat(100_000) + self.data.flashloan_admin_commission + self.data.flashloan_deposit_commission), sp.nat(100_000))
        )

        with sp.if_(self.data.totalSupply > sp.nat(0)):
            self.data.deposit_index += (
                self.data.flashloan_deposit_commission * convert_mutez_to_nat(requested_xtz) * FIXED_POINT_FACTOR / self.data.totalSupply / sp.nat(100_000)
            )

        sp.transfer(sp.unit, requested_xtz, params.callback)
        call_self_entry('flashloanFinalize')

    @sp.entry_point
    def flashloanReturn(self):
        new_flashloan_amount = sp.local('new_flashloan_amount', sp.sub_mutez(self.data.flashloan_amount, sp.amount))
        with sp.if_(new_flashloan_amount.value.is_some()):
            self.data.flashloan_amount = new_flashloan_amount.value.open_some()
        with sp.else_():
            self.data.flashloan_amount = sp.mutez(0)

    @sp.entry_point
    def flashloanFinalize(self):
        sp.verify(self.data.flashloan_amount == sp.mutez(0), 'loan error')


sp.add_compilation_target('contract', LeveragedFarmLendingSmartContract(
    sp.address(ADMIN_ADDRESS),
    sp.address(LIQUIDITY_BAKING_ADDRESS),
    sp.address(FA_TZBTC_ADDRESS),
    sp.address(FA_LB_TOKEN_ADDRESS),
    sp.address(ORACLE_ADDRESS),
))
