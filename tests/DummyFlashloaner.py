import smartpy as sp
import os


class DummyFlashloaner(sp.Contract):

    def __init__(self, kord_contract, fa_tzBTC_address):
        self.init(
            kord_contract = kord_contract,
            fa_tzBTC_address = fa_tzBTC_address,
            return_amount = sp.mutez(0),
            balance = sp.mutez(0),
            return_shares = sp.nat(0),
            tzBTC_shares = sp.nat(0),
        )

    @sp.entry_point
    def default(self):
        pass

    @sp.entry_point
    def callback_xtz(self):
        self.data.balance = sp.balance

        handle = sp.contract(
            sp.TUnit,
            self.data.kord_contract,
            entry_point = 'flashloanReturn'
        ).open_some('cant call flashloanReturn')

        sp.transfer(sp.unit, self.data.return_amount, handle)

    @sp.entry_point
    def try_flashloan_xtz(self, params):
        sp.set_type(params,
            sp.TRecord(return_amount=sp.TMutez, requested_amount=sp.TMutez).
            layout(('return_amount', 'requested_amount'))
        )
        self.data.return_amount = params.return_amount

        callback = sp.contract(sp.TUnit, sp.self_address, "callback_xtz").open_some()

        handle = sp.contract(
            sp.TRecord(
                callback = sp.TContract(sp.TUnit),
                requested_xtz = sp.TMutez,
            ).layout(('callback', 'requested_xtz')),
            self.data.kord_contract,
            entry_point = 'flashloan'
        ).open_some('cant call flashloan')

        params = sp.record(
            callback = callback,
            requested_xtz = params.requested_amount,
        )

        sp.transfer(params, sp.mutez(0), handle)

    @sp.entry_point
    def set_btc_fa(self, address):
        sp.set_type(address, sp.TAddress)
        self.data.fa_tzBTC_address = address

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

    @sp.entry_point
    def callback_btc(self):
        self.update_tzBTC_shares()

        self.approve_tzBTC_shares(self.data.kord_contract, self.data.return_shares)

        handle = sp.contract(
            sp.TNat,
            self.data.kord_contract,
            entry_point = 'flashloanReturn'
        ).open_some('cant call flashloanReturn')

        sp.transfer(self.data.return_shares, sp.mutez(0), handle)

        self.approve_tzBTC_shares(self.data.kord_contract, sp.nat(0))

    @sp.entry_point
    def try_flashloan_btc(self, params):
        sp.set_type(params,
            sp.TRecord(return_shares=sp.TNat, requested_shares=sp.TNat).
            layout(('return_shares', 'requested_shares'))
        )
        self.data.return_shares = params.return_shares

        callback = sp.contract(sp.TUnit, sp.self_address, "callback_btc").open_some()

        handle = sp.contract(
            sp.TRecord(
                callback = sp.TContract(sp.TUnit),
                requested_shares = sp.TNat,
            ).layout(('callback', 'requested_shares')),
            self.data.kord_contract,
            entry_point = 'flashloan'
        ).open_some('cant call flashloan')

        params = sp.record(
            callback = callback,
            requested_shares = params.requested_shares,
        )

        sp.transfer(params, sp.mutez(0), handle)

    def update_tzBTC_shares(self):
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
            callback = sp.self_entry_point(entry_point = 'updateTzBTCCallback'),
        )

        sp.transfer(params, sp.mutez(0), handle)

    @sp.entry_point
    def updateTzBTCCallback(self, tzBTC_shares):
        sp.set_type(tzBTC_shares, sp.TNat)
        self.data.tzBTC_shares = tzBTC_shares


address = sp.address('tz1VGzxpbAcP1CL5z8f8CZNGALFtMFCcakrX')
sp.add_compilation_target('contract', DummyFlashloaner(address, address))
