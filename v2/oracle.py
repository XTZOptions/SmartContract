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
    def getDataFromOrO(self,params):
        
        data = sp.record(price=0)
        contract = sp.contract(sp.TRecord( price = sp.TNat),sp.sender,entry_point = "receiveDataFromOrO").open_some()
        data.price = self.data.xtzPrice

        sp.if sp.amount == sp.mutez(100):
            sp.transfer(data,sp.mutez(0),contract)
        sp.else:
            sp.transfer(data,sp.amount,contract)


@sp.add_test(name="XTZOracle Testing")
def test():
    scenario = sp.test_scenario()
    admin = sp.test_account("Alice")

    oracle = XTZOracle(admin.address)
    scenario += oracle
    
    scenario += oracle.feedData(price=400).run(sender=admin)
    scenario += oracle.feedData(price=600).run(sender=admin)
    
    # scenario += oracle.feedData(currency = "INR", buy = 545791 , sell = 545791).run(sender=sp.address('tz1-AAA'))
    # scenario += oracle.addDataContributor(contributor=sp.address("tz1-AAA")).run(sender=sp.address('tz1beX9ZDev6SVVW9yJwNYA89362ZpWuDwou'))
    # scenario += oracle.feedData(currency = "INR", buy = 545791 , sell = 545791).run(sender=sp.address('tz1-AAA'))
    # # scenario += oracle.getDataFromOrO(currency = "INR").run(sender=sp.address("KT1-AAA") , amount = sp.mutez(5000))
    # scenario += oracle.getDataFromOrO(currency = "INR").run(sender=sp.address("KT1-BBB") , amount = sp.mutez(4000))