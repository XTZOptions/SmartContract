import smartpy as sp

class XTZOracle(sp.Contract):
    def __init__(self, admin):
        
        self.init(xtzPrice = sp.nat(0), keysset = sp.set([admin]) , owner = admin)
    
    @sp.entry_point
    def feedData(self,params):
        sp.if (self.data.keysset.contains(sp.sender)):
            self.data.xtzPrice = params.price 
            
    @sp.entry_point
    def addDataContributor(self,params):
        sp.if sp.sender == self.data.owner:
            self.data.keysset.add(params.contributor)
            
    @sp.entry_point
    def getDataMint(self,params):
    
        data = sp.record(price=sp.to_int(self.data.xtzPrice),address=params.address,amount=params.amount)
        
        contract = sp.contract(sp.TRecord( price = sp.TInt,address = sp.TAddress, amount = sp.TInt),sp.sender,entry_point = "OrOMint").open_some()
        
        sp.if sp.amount == sp.mutez(100):
            sp.transfer(data,sp.mutez(0),contract)
        # sp.else:
        #     sp.transfer(data,sp.amount,contract)

class ALAToken(sp.Contract):
    def __init__(self, admin,oro):
        self.init(paused = False, ledger = sp.big_map(tvalue = sp.TRecord(approvals = sp.TMap(sp.TAddress, sp.TNat), balance = sp.TNat)), administrator = admin, totalSupply = 0
        ,contract= sp.set([admin]),OrO=oro)

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


    def addAddressIfNecessary(self, address):
        sp.if ~ self.data.ledger.contains(address):
            self.data.ledger[address] = sp.record(balance = 0, approvals = {})
    
@sp.add_test(name="XTZOracle Testing")
def test():
    scenario = sp.test_scenario()
    
    admin = sp.test_account("Alice")
    alice = sp.test_account("Alice")
    bob   = sp.test_account("Robert")

    oracle = XTZOracle(admin.address)
    scenario += oracle
    
    token = ALAToken(admin.address,oracle.address)
    scenario += token 

    scenario += oracle.feedData(price=400).run(sender=admin)
    scenario += oracle.feedData(price=600).run(sender=admin)

    
    
    scenario += token.mint(value=10).run(sender=alice,amount=sp.tez(10))
    #scenario += oracle.getDataMint(address=alice.address,amount=10).run(sender=alice)