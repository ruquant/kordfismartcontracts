import smartpy as sp

class DummyOracle(sp.Contract):
    """
    Use in contract:

        sp.view("get_price", self.data.common_oracle, 'XTZ', t=sp.TNat).open_some('invalid view')
        sp.view("get_price", self.data.common_oracle, 'BTC', t=sp.TNat).open_some('invalid view')
    """
    def __init__(self, xtz_price, btc_price):
        self.init(
            prices=sp.map(l = {
                "XTZ": xtz_price,
                "BTC": btc_price,
            }, tkey=sp.TString, tvalue=sp.TNat),
        )
    
    @sp.entry_point
    def default(self):
        pass

    @sp.entry_point
    def set_price(self, params):
        sp.set_type(params,
            sp.TRecord(xtz_price=sp.TNat, btc_price=sp.TNat).
            layout(("xtz_price", "btc_price"))
        )

        self.data.prices["XTZ"] = params.xtz_price
        self.data.prices["BTC"] = params.btc_price

    @sp.onchain_view()
    def get_price(self, symbol):
        sp.set_type(symbol, sp.TString)
        sp.result(self.data.prices[symbol])

sp.add_compilation_target('contract', DummyOracle(1_530_000, 21_520_000_000))
