from copy import deepcopy


from ..constants import ALICE_ADDRESS, ALICE_KEY, BOB_ADDRESS, BOB_KEY, CLARE_ADDRESS, CLARE_KEY, CONTRACT_ADDRESS, TEST_GAS_DELTA


FIXED_POINT_PRECISION = 12  # must be greater than 6
FIXED_POINT_FACTOR = 10 ** FIXED_POINT_PRECISION
INITIAL_INDEX_VALUE = FIXED_POINT_FACTOR

DEFAULT_RATE_1 = 3022   # 10% annual rate
DEFAULT_RATE_2 = 12857  # 50% annual rate
DEFAULT_TRESHOLD_PERCENT_1 = 80
DEFAULT_TRESHOLD_PERCENT_2 = 90


INFINITY_NAT = 10 ** 18


DEFAULT_RATE_PARAMS = {
    'rate_1': DEFAULT_RATE_1,
    'rate_diff': DEFAULT_RATE_2 - DEFAULT_RATE_1,
    'threshold_percent_1': DEFAULT_TRESHOLD_PERCENT_1,
    'threshold_percent_2': DEFAULT_TRESHOLD_PERCENT_2,
}


LINEAR_RATE_PARAMS = {
    'rate_1': 5 * 10 ** (FIXED_POINT_PRECISION - 1),
    'rate_diff': 5 * 10 ** (FIXED_POINT_PRECISION - 1),
    'threshold_percent_1': 50,
    'threshold_percent_2': 50,
}


CONST_RATE_PARAMS = {
    'rate_1': DEFAULT_RATE_1,
    'rate_diff': 0,
    'threshold_percent_1': 0,
    'threshold_percent_2': 100,    
}


DEFAULT_STORAGE = {
    'index_update_dttm': 0,
    'gross_credit_index': INITIAL_INDEX_VALUE,
    'deposit_index': INITIAL_INDEX_VALUE,
    'net_credit_index': INITIAL_INDEX_VALUE,
    'upfront_commission': 1_000,
    'is_working': True,
    'index_delta': 0,
    'lb_price': 1_000_000_000_000,
    'lb_price_change_rate': 5_787_000,

    'onchain_liquidation_available': True,
    'onchain_liquidation_percent': 120,  # 120%
    'onchain_liquidation_comm': 50,  # 50%
    'max_leverage': 40,
    'liquidation_percent': 120,  # 120%
    'liquidation_price_percent': 110, # 110%
    'liquidation_comm': 50,  # 50%

    'total_gross_credit': 0,
    'total_net_credit': 0,
    'totalSupply': 0,

    'rate_params': DEFAULT_RATE_PARAMS,
    'ledger': {},
    'administrator': ALICE_ADDRESS,

    'liquidity_baking_address': ALICE_ADDRESS,
    'dex_contract_address': ALICE_ADDRESS,
    'fa_tzBTC_address': ALICE_ADDRESS,
    'fa_lb_address': ALICE_ADDRESS,
    'oracle_address': ALICE_ADDRESS,

    'liquidity_book': {},

    'lb_shares': 0,
    'local_params': {
        'fa_tzBTC_callback_status': False,
        'fa_lb_callback_status': False,
        'tzbtc_pool': 0,
        'lqt_total': 0, 
    },

    'flashloan_available': False,
    'flashloan_admin_commission': 100,
    'flashloan_deposit_commission': 50,
    'flashloan_amount': 0,

    'metadata': {},
    'token_metadata': {},
}


BTC_DEFAULT_STORAGE = deepcopy(DEFAULT_STORAGE)
BTC_DEFAULT_STORAGE['tzBTC_shares'] = 0

BTC_DEFAULT_STORAGE['flashloan_shares'] = 0
del BTC_DEFAULT_STORAGE['flashloan_amount']
