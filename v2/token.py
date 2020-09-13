import smartpy as sp

class ALAToken(sp.Contract):
    def __init__(self, admin):
        self.init(paused = False, ledger = sp.big_map(tvalue = sp.TRecord(approvals = sp.TMap(sp.TAddress, sp.TNat), balance = sp.TNat)), administrator = admin, totalSupply = 0
        ,contract= sp.set([admin]),xtzPrice=400)

    @sp.entry_point
    def transfer(self, params):
        sp.set_type(params, sp.TRecord(from_ = sp.TAddress, to_ = sp.TAddress, value = sp.TNat).layout(("from_ as from", ("to_ as to", "value"))))
        sp.verify((sp.sender == self.data.administrator) |
            (~self.data.paused &
                ((params.from_ == sp.sender) |
                 (self.data.ledger[params.from_].approvals[sp.sender] >= params.value))))
        self.addAddressIfNecessary(params.to_)
        sp.verify(self.data.ledger[params.from_].balance >= params.value)
        self.data.ledger[params.from_].balance = sp.as_nat(self.data.ledger[params.from_].balance - params.value)
        self.data.ledger[params.to_].balance += params.value
        sp.if (params.from_ != sp.sender) & (self.data.administrator != sp.sender):
            self.data.ledger[params.from_].approvals[sp.sender] = sp.as_nat(self.data.ledger[params.from_].approvals[sp.sender] - params.value)

    @sp.entry_point
    def approve(self, params):
        sp.set_type(params, sp.TRecord(spender = sp.TAddress, value = sp.TNat).layout(("spender", "value")))
        sp.verify(~self.data.paused)
        alreadyApproved = self.data.ledger[sp.sender].approvals.get(params.spender, 0)
        sp.verify((alreadyApproved == 0) | (params.value == 0), "UnsafeAllowanceChange")
        self.data.ledger[sp.sender].approvals[params.spender] = params.value

    @sp.entry_point
    def setPause(self, params):
        sp.set_type(params, sp.TBool)
        sp.verify(sp.sender == self.data.administrator)
        self.data.paused = params

    @sp.entry_point
    def setAdministrator(self, params):
        sp.set_type(params, sp.TAddress)
        sp.verify(sp.sender == self.data.administrator)
        self.data.administrator = params

    
    @sp.entry_point
    def mint(self, params):
        sp.verify(params.value>0)
        tezValue=sp.tez(sp.as_nat(params.value))
        sp.verify(sp.amount == tezValue)
        
        c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TInt), self.data.OrO, entry_point = "getDataMint").open_some()
        mydata = sp.record(address = sp.sender,amount=params.value)

        sp.transfer(mydata, sp.mutez(100), c)

    @sp.entry_point
    def OrOMint(self,params):
        sp.verify(sp.sender == self.data.OrO )
        self.addAddressIfNecessary(params.address)
        sp.verify(params.price>0)
        sp.verify(params.amount>0)
        
        self.data.ledger[params.address].balance += abs(params.price*params.amount*100)

        self.data.totalSupply += abs(params.price*params.amount*100)
        
    
    @sp.entry_point
    def burn(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress, value = sp.TNat))
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(self.data.ledger[params.address].balance >= params.value)
        self.data.ledger[params.address].balance = sp.as_nat(self.data.ledger[params.address].balance - params.value)
        self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.value)

    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.ledger.contains(address):
            self.data.ledger[address] = sp.record(balance = 0, approvals = {})


    @sp.entry_point
    def AddContract(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.contract.add(params) 

    @sp.entry_point
    def RemoveContract(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.contract.remove(params)

    @sp.entry_point
    def LockToken(self,params):
        sp.verify(self.data.contract.contains(sp.sender))
        sp.verify(self.data.ledger.contains(params.address))
        sp.verify(self.data.ledger[params.address].balance >= params.amount)
        self.data.ledger[params.address].balance = abs(self.data.ledger[params.address].balance - params.amount)

    @sp.entry_point
    def UnlockToken(self,params):
        sp.verify(self.data.contract.contains(sp.sender))
        sp.verify(self.data.ledger.contains(params.address))
        self.data.ledger[params.address].balance += params.amount

    # @sp.entry_point
    # def withdrawToken(self,params):
    #     sp.verify(params.amount > 0)
    #     sp.verify(self.data.ledger.contains(sp.sender))
    #     sp.verify(self.data.ledger[sp.sender].balance >= params.amount)
    #     self.data.ledger[sp.sender].balance = sp.as_nat(self.data.ledger[sp.sender].balance - params.amount)
    #     self.data.totalSupply = sp.as_nat(self.data.totalSupply - params.amount)
    #     sp.send(sp.sender,sp.mutez(params.amount*100))
        
    @sp.entry_point
    def ModifyPrice(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.xtzPrice = params.price

    @sp.view(sp.TNat)
    def getBalance(self, params):
        sp.result(self.data.ledger[params].balance)

    @sp.view(sp.TNat)
    def getAllowance(self, params):
        sp.result(self.data.ledger[params.owner].approvals[params.spender])

    @sp.view(sp.TNat)
    def getTotalSupply(self, params):
        sp.set_type(params, sp.TUnit)
        sp.result(self.data.totalSupply)

    @sp.view(sp.TAddress)
    def getAdministrator(self, params):
        sp.set_type(params, sp.TUnit)
        sp.result(self.data.administrator)

class Viewer(sp.Contract):
    def __init__(self, t):
        self.init(last = sp.none)
        self.init_type(sp.TRecord(last = sp.TOption(t)))
    @sp.entry_point
    def target(self, params):
        self.data.last = sp.some(params)

class Api(sp.Contract):

    def __init__(self,token):
        self.init(tokenContract=token)


    @sp.entry_point
    def Add(self,params):
        self.Payment(params.address,params.amount)
    
    def Lock(self,address,amount):
        c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TNat), self.data.tokenContract, entry_point = "LockToken").open_some()
        mydata = sp.record(address = address,amount=amount)
        sp.transfer(mydata, sp.mutez(0), c)
    
    def Unlock(self,address,amount):
        c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TNat), self.data.tokenContract, entry_point = "UnlockToken").open_some()
        mydata = sp.record(address = address,amount=amount)
        sp.transfer(mydata, sp.mutez(0), c)
    
    

@sp.add_test(name = "ALA Token")
def test():

    scenario = sp.test_scenario()
    
    admin = sp.address("tz1LAWQmxJcnK43vR9G8jsNTzR6b2unZ58NX")
    alice = sp.test_account("Alice")
    bob   = sp.test_account("Robert")


    c1 = ALAToken(admin)
    c2 = Api(c1.address)
    scenario += c1
    scenario += c2
    
    scenario += c1.mint(address = alice.address, value = 12).run(sender = alice,amount = sp.tez(12))
    scenario += c1.ModifyPrice(price=500).run(sender=admin)
    scenario += c1.mint(address = bob.address, value = 3).run(sender = admin,amount=sp.tez(3))
    # scenario += c1.mint(address = alice.address, value = 3).run(sender = admin)
    scenario += c1.AddContract(c2.address).run(sender=admin)
    scenario += c2.Add(address=alice.address,amount=550).run(sender=alice)
    
    
    # scenario += c1.UnlockToken(address=bob.address,amount=100).run(sender=alice)
    # scenario += c1.LockToken(address=bob.address,amount=100).run(sender=alice)
    # scenario += c1.RemoveContract(alice.address).run(sender=admin)
    