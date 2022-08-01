from decimal import Decimal, getcontext


class Contract(object):
    """
    Reproduce LB DEX calculations for storage parameters
    """
    def __init__(self, tokenPool: int, xtzPool: int, lqtTotal: int):
        self.tokenPool = tokenPool
        self.xtzPool = xtzPool
        self.lqtTotal = lqtTotal

    def __repr__(self):
        return f"Contract({self.tokenPool}, {self.xtzPool}, {self.lqtTotal})"

    def xtz_to_token_result(self, amount: int):
        # Y = 0.999 * X * 999 * tokenPool / (1000 * xtzPool + 0.999 * X * 999)
        # new_xtzPool = xtzPool + 0.999 * X
        # new_tokenPool = tokenPool - Y
        amount_net_burn = amount * 999 // 1000
        tokens = amount_net_burn * 999 * self.tokenPool // (self.xtzPool * 1000 + amount_net_burn * 999)
        self.tokenPool -= tokens
        self.xtzPool += amount_net_burn
        return tokens

    def add_liquidity_result(self, amount: int):
        # tokens_deposited = ceildiv(amount * tokenPool, xtzPool)
        # lqt_minted = amount * storage.lqtTotal  / xtzPool
        tokens_deposited = int(_ceil_decimal(Decimal(amount * self.tokenPool) / Decimal(self.xtzPool)))
        lqt_minted = amount * self.lqtTotal // self.xtzPool
        self.tokenPool += tokens_deposited
        self.xtzPool += amount
        self.lqtTotal += lqt_minted
        return tokens_deposited
    
    def remove_liquidity_result(self, lqtBurned):
        # xtz_withdrawn = lqtBurned * storage.xtzPool / storage.lqtTotal
        # tokens_withdrawn = lqtBurned * storage.tokenPool /  storage.lqtTotal
        xtz_withdrawn = lqtBurned * self.xtzPool // self.lqtTotal
        tokens_withdrawn = lqtBurned * self.tokenPool // self.lqtTotal
        self.lqtTotal -= lqtBurned
        self.xtzPool -= xtz_withdrawn
        self.tokenPool -= tokens_withdrawn
        return tokens_withdrawn, xtz_withdrawn

    def token_to_xtz_result(self, tokensSold):
        # xtz_bought = ((tokensSold * 999n * storage.xtzPool) / (storage.tokenPool * 1000n + (tokensSold * 999n)))
        # xtz_bought_net_burn = (xtz_bought * 999n) / 1000n
        xtz_bought = tokensSold * 999 * self.xtzPool // (self.tokenPool * 1000 + tokensSold * 999)
        xtz_bought_net_burn = xtz_bought * 999 // 1000
        self.xtzPool -= xtz_bought
        self.tokenPool += tokensSold
        return xtz_bought_net_burn


def get_invest_params(tokenPool, xtzPool, lqtTotal, invest_amount):
    """
    Return minimal invest params which are converted to maximum LB value for invest_amount.
    """
    xtz2token = get_xtz_to_token_parameter(tokenPool, xtzPool, lqtTotal, invest_amount)
    contract = Contract(tokenPool, xtzPool, lqtTotal)
    tokens = contract.xtz_to_token_result(xtz2token)

    def f(xtz2lqt):
        temp_contract = Contract(contract.tokenPool, contract.xtzPool, contract.lqtTotal)
        return temp_contract.add_liquidity_result(xtz2lqt) - tokens
    xtz2lqt = _binary_search(f, invest_amount - xtz2token)

    start_lqt = contract.lqtTotal
    contract.add_liquidity_result(xtz2lqt)
    lqtMinted = contract.lqtTotal - start_lqt

    return xtz2token, tokens, xtz2lqt, lqtMinted

def get_client_invest_params(tokenPool, xtzPool, lqtTotal, xtz_invest, leverage, commission):
    """
    Invest parameters for amount with commission xtz_invest and leverage.
    """
    user_amount = int(xtz_invest * 100 / (100 + commission * (leverage - 1)))
    invest_amount = int(user_amount * leverage)
    xtz2token, tokens, xtz2lqt, lqtMinted = get_invest_params(tokenPool, xtzPool, lqtTotal, invest_amount)
    if xtz_invest > xtz2token + xtz2lqt:
        return (xtz2token + xtz2lqt, xtz2token, tokens, xtz2lqt, lqtMinted)
    return (xtz_invest, xtz2token, tokens, xtz2lqt, lqtMinted)

def get_xtz_to_token_parameter(tokenPool, xtzPool, lqtTotal, invest_amount):
    """
    Calculate maximum of tzBTC tokens that can be deposited to liquidity with invest_amount.
    Return the amount that should be spent to token transfer.

    invest_amount = xtz2token + xtz2lqt
    xtz_to_contract_result(xtz2token) = add_liquidity_result(xtz2lqt)
    return min of such xtz2token
    """
    def f(xtz2token):
        contract = Contract(tokenPool, xtzPool, lqtTotal)
        tokens = contract.xtz_to_token_result(xtz2token)
        return tokens - contract.add_liquidity_result(invest_amount - xtz2token)

    return _binary_search(f, invest_amount)


def _ceil_decimal(d: Decimal) -> int:
    # for non-negative d
    assert d >= 0
    x = int(d)
    remainder = d - x
    return x if remainder == 0 else x + 1


def _binary_search(f, high):
    # binary search of minimal x such that f(x) = 0
    # suppose such x exists between 0 and high
    lo = 0
    hi = high
    while lo < hi:
        mid = (lo + hi) // 2
        if f(mid) < 0:
            lo = mid + 1
        else:
            hi = mid

    return lo

def get_lb_tokens_value(tokenPool, xtzPool, lqtTotal, lb_tokens):
    contract = Contract(tokenPool, xtzPool, lqtTotal)
    tzbtc_tokens, xtz_amount = contract.remove_liquidity_result(lb_tokens)
    return xtz_amount + contract.token_to_xtz_result(tzbtc_tokens)
