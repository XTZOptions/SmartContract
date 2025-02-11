import smartpy as sp

class ALACoin(sp.Contract):
    def __init__(self, admin):
        self.init(balances = sp.big_map(), administrator = admin, totalSupply = 0,contract= sp.set([admin]))

    @sp.entry_point
    def transfer(self, params):
        sp.verify((sp.sender == self.data.administrator) |
            (((params.fromAddr == sp.sender) |
                 (self.data.balances[params.fromAddr].approvals[sp.sender] >= params.amount))))
        
        self.addAddressIfNecessary(params.toAddr)
        sp.verify(self.data.balances[params.fromAddr].balance >= params.amount)
        self.data.balances[params.fromAddr].balance -= params.amount
        self.data.balances[params.toAddr].balance += params.amount
        sp.if (params.fromAddr != sp.sender) & (self.data.administrator != sp.sender):
            self.data.balances[params.fromAddr].approvals[params.toAddr] -= params.amount


    @sp.entry_point
    def approve(self, params):
        sp.verify((sp.sender == self.data.administrator) |
                  (params.fromAddr == sp.sender))
        sp.verify(self.data.balances[params.fromAddr].approvals.get(params.toAddr, 0) == 0)
        self.data.balances[params.fromAddr].approvals[params.toAddr] = params.amount

    @sp.entry_point
    def setAdministrator(self, params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.administrator = params

    @sp.entry_point
    def mint(self, params):

        tezValue=sp.tez(sp.as_nat(params.amount))
        sp.verify(sp.amount == tezValue)
        self.addAddressIfNecessary(params.address)
        self.data.balances[params.address].balance += params.amount*10000
        self.data.totalSupply += params.amount*10000

    @sp.entry_point
    def withdraw(self):
        sp.verify(self.data.balances.contains(sp.sender))
        sp.send(sp.sender,sp.tez(1))

        self.data.balances[sp.sender].balance = sp.to_int(self.data.balances[sp.sender].balance % 10000)
    
    @sp.entry_point
    def burn(self, params):
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(self.data.balances[params.address].balance >= params.amount)
        self.data.balances[params.address].balance -= params.amount
        self.data.totalSupply -= params.amount

    @sp.entry_point
    def LockToken(self,params):
        sp.verify(self.data.contract.contains(sp.sender))
        sp.verify(self.data.balances[params.address].balance >= params.amount)
        self.data.balances[params.address].balance -= params.amount

    @sp.entry_point
    def UnlockToken(self,params):
        sp.verify(self.data.contract.contains(sp.sender))
        self.data.balances[params.address].balance += params.amount
    
    @sp.entry_point
    def AddContract(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.contract.add(params)  
    
    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.balances.contains(address):
            self.data.balances[address] = sp.record(balance = 0, approvals = {})



@sp.add_test(name = "ALA Coin")
def test():

    scenario = sp.test_scenario()
    scenario.h1("ALA Contract")
    value = 1
    admin = sp.address("tz123")
    alice = sp.address("tz1456")
    bob   = sp.address("tz1678")


    c1 = ALACoin(admin)

    scenario += c1
    scenario += c1.mint(address = alice, amount = 12).run(sender = alice,amount = sp.tez(12))
    scenario += c1.mint(address = bob, amount = 10).run(sender = alice,amount = sp.tez(10))
    
    
    scenario += c1.AddContract(bob).run(sender=admin)
    scenario += c1.LockToken(address = bob, amount = 10).run(sender = bob)
    scenario += c1.UnlockToken(address = bob, amount = 10).run(sender = bob)

    scenario += c1.withdraw().run(sender = bob)