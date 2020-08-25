import smartpy as sp 


class Token(sp.Contract):
    def __init__(self, admin):
        self.init(balances = sp.big_map(), administrator = admin, totalSupply = 0,contract= sp.big_map())

    @sp.entry_point
    def mint(self, params):

        tezValue=sp.tez(sp.as_nat(params.amount))
        sp.verify(sp.amount == tezValue)
        self.addAddressIfNecessary(sp.sender)
        self.data.balances[sp.sender].balance += params.amount*10000
        self.data.totalSupply += params.amount*10000

    @sp.entry_point
    def LockToken(self,params):
        sp.verify(self.data.contract.contains(sp.sender))
        self.data.balances[params.address].balance -= params.amount 


    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.balances.contains(address):
            self.data.balances[address] = sp.record(balance = 0, approvals = {})

    @sp.entry_point
    def AddContract(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.contract[params] = 1  

class Api(sp.Contract):
    
    def __init__(self, admin,token):
        self.init(tokenContract=token, administrator = admin, totalSupply = 0)

    @sp.entry_point
    def TokenPayment(self):
        c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TInt), self.data.tokenContract, entry_point = "LockToken").open_some()
        mydata = sp.record(address = sp.sender,amount=10)
        sp.transfer(mydata, sp.amount, c)
        
@sp.add_test(name = "Token Testing")
def test():

    scenario = sp.test_scenario()
    admin = sp.address("tz123")
    alice = sp.address("tz1456")


    c1 = Token(admin)
    c2 = Api(admin,c1.address)
    scenario += c1 
    scenario += c2
    
    scenario += c1.mint(amount=10).run(sender=alice,amount=sp.tez(10))
    
    scenario += c1.AddContract(c2.address).run(sender=admin)

    scenario += c2.TokenPayment().run(sender=alice)