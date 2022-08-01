from math import ceil
from .xtz_invest_params import Contract, _binary_search


def calculate_converted_xtz(contract, xtz, tokens):
    """
    Amount of xtz that converted to tzBTC (or reverse) and then added to liquidity
    that consumes all xtz + tokens value.
    """
    def f(xtz2lqt):
        temp_contract = Contract(contract.tokenPool, contract.xtzPool, contract.lqtTotal)
        if xtz2lqt >= xtz:
            tzbtc_to_convert = calculate_required_tzbtc(temp_contract, xtz2lqt - xtz)
            temp_contract.token_to_xtz_result(tzbtc_to_convert)
            tzbtc_invested = temp_contract.add_liquidity_result(xtz2lqt)
            return tzbtc_invested - (tokens - tzbtc_to_convert)
        else:
            tzbtc_converted = temp_contract.xtz_to_token_result(xtz - xtz2lqt)
            tzbtc_invested = temp_contract.add_liquidity_result(xtz2lqt)
            return tzbtc_invested - (tokens + tzbtc_converted)
    invest_xtz = _binary_search(f, contract.xtzPool)
    return xtz - invest_xtz


def calculate_required_tzbtc(contract, xtz):
    """
    Minimal tzBTC amount for contract converted to xtz amount
    """
    def f(btc2xtz):
        temp_contract = Contract(contract.tokenPool, contract.xtzPool, contract.lqtTotal)
        return temp_contract.token_to_xtz_result(btc2xtz) - xtz
    return _binary_search(f, contract.tokenPool)


def get_invest_params(tokenPool, xtzPool, lqtTotal, xtz_invest, tzbtc_loan, commission):
    """
    Invest parameters for amount without commission xtz_invest and loaned tzBTC tzbtc_loan.
    """
    contract = Contract(tokenPool, xtzPool, lqtTotal)
    xtz_to_convert = calculate_converted_xtz(contract, xtz_invest, tzbtc_loan)
    xtz2lqt = xtz_invest - xtz_to_convert
    if xtz_to_convert >= 0:
        minTokens = contract.xtz_to_token_result(xtz_to_convert)
        start_lqt = contract.lqtTotal
        contract.add_liquidity_result(xtz2lqt)
        lqtMinted = contract.lqtTotal - start_lqt
        tzBTC2xtz = 0
        minXtz = 0
        # formula tip:
        # amount = amount2tzBTC + amount2Lqt + upfront_commission
        # upfront_commission = max((2 * amount2Lqt - amount), 0) * commission / (100 - commission)
        if xtz2lqt <= xtz_to_convert:
            upfront_commission = 0
        else:
            upfront_commission = (xtz2lqt - xtz_to_convert) * commission // 100
        amount = xtz2lqt + xtz_to_convert + upfront_commission
    else:
        tzBTC2xtz = calculate_required_tzbtc(contract, -xtz_to_convert)
        minXtz = contract.token_to_xtz_result(tzBTC2xtz)
        start_lqt = contract.lqtTotal
        contract.add_liquidity_result(xtz2lqt)
        lqtMinted = contract.lqtTotal - start_lqt
        xtz_to_convert = 0
        minTokens = 0
        # formula tip
        # amount = invest_xtz + upfront_commission
        # amount - invest_xtz = upfront_commission = (2 * amount2Lqt - amount) * commission / (100 - commission)
        amount = ceil((2 * xtz2lqt * commission + xtz_invest * (100 - commission)) / 100)

    return amount, xtz_to_convert, minTokens, tzBTC2xtz, minXtz, xtz2lqt, lqtMinted

def get_client_invest_params(tokenPool, xtzPool, lqtTotal, xtz_invest, leverage, commission):
    """
    Invest parameters for amount with commission xtz_invest and leverage.
    """
    # tips:
    # invest + upfront_commission = xtz_invest
    # upfront_commission = (2 * amount2Lqt - xtz_invest) * commission / (100 - commission)
    # leverage = 2 * (tzBTC_delta - tzBTC2xtz) / (tzBTC_delta - 2 * tzBTC2xtz)

    if leverage == 1:
        # if `xtz2lqt * 2 > xtz_invest` we will take commission even with leverage 1
        # this situation exists in case when user invests more than 0.1% of liquidity pool
        def f(invest):
            amount, xtz2token, tokens, tzBTC2xtz, minXtzBought, xtz2lqt, lqtMinted = get_invest_params(
                tokenPool, xtzPool, lqtTotal, invest, 0, commission)
            return amount - xtz_invest
        real_invest = _binary_search(f, xtz_invest)
        return get_invest_params(tokenPool, xtzPool, lqtTotal, real_invest, 0, commission)

    def find_invest(invest):
        temp_contract = Contract(tokenPool, xtzPool, lqtTotal)
        upfront_commission_upper_bound = xtz_invest - invest
        amount2Lqt_upper_bound = int(((100 - commission) * upfront_commission_upper_bound / commission + xtz_invest) / 2)
        if amount2Lqt_upper_bound <= invest:
            xtz_to_convert = invest - amount2Lqt_upper_bound
            minTokens = temp_contract.xtz_to_token_result(xtz_to_convert)
            tokens = temp_contract.add_liquidity_result(amount2Lqt_upper_bound)
            tzBTC_delta = tokens - minTokens
            # leverage = 2 * amount2Lqt_upper_bound / invest
            return leverage - 2 * amount2Lqt_upper_bound / invest
        else:
            tzBTC2xtz = calculate_required_tzbtc(temp_contract, amount2Lqt_upper_bound - invest)
            minXtz = temp_contract.token_to_xtz_result(tzBTC2xtz)
            tokens = temp_contract.add_liquidity_result(amount2Lqt_upper_bound)
            tzBTC_delta = tzBTC2xtz + tokens
             # leverage = 2 * (tzBTC_delta - tzBTC2xtz) / (tzBTC_delta - 2 * tzBTC2xtz)
            return leverage - 2 * (tzBTC_delta - tzBTC2xtz) / (tzBTC_delta - 2 * tzBTC2xtz)

    # find maximum invest value, that doesn't exceed leverage
    invest_without_commission = _binary_search(find_invest, xtz_invest)

    contract = Contract(tokenPool, xtzPool, lqtTotal)
    upfront_commission = xtz_invest - invest_without_commission
    xtz2lqt = int(((100 - commission) * upfront_commission / commission + xtz_invest) / 2)
    xtz_to_convert = invest_without_commission - xtz2lqt
    if xtz_to_convert >= 0:
        minTokens = contract.xtz_to_token_result(xtz_to_convert)
        start_lqt = contract.lqtTotal
        contract.add_liquidity_result(xtz2lqt)
        lqtMinted = contract.lqtTotal - start_lqt
        tzBTC2xtz = 0
        minXtz = 0
        # upfront_commission = (2 * amount2Lqt - xtz_invest) * commission / (100 - commission)
        upfront_commission = (xtz2lqt - xtz_to_convert) * commission // 100
        # adjust "sent amount error"
        xtz_to_convert = (xtz_invest - upfront_commission - xtz2lqt)
    else:
        tzBTC2xtz = calculate_required_tzbtc(contract, -xtz_to_convert)
        minXtz = contract.token_to_xtz_result(tzBTC2xtz)
        start_lqt = contract.lqtTotal
        contract.add_liquidity_result(xtz2lqt)
        lqtMinted = contract.lqtTotal - start_lqt
        xtz_to_convert = 0
        minTokens = 0

    return xtz_invest, xtz_to_convert, minTokens, tzBTC2xtz, minXtz, xtz2lqt, lqtMinted
