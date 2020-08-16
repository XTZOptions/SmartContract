import smartpy as sp

class PutContract(sp.Contract):
    def __init__(self,admin,end_date):
        self.init(contractBuyer=sp.big_map(),liquidityPool=sp.map(),administrator = admin,
        totalLiquidity=sp.nat(0),end_date=sp.timestamp(end_date),
        xtzPrice=300)

    @sp.entry_point
    def putBuyer(self, params):
        sp.verify(~self.data.contractBuyer.contains(sp.sender))
        sp.verify((params.strikePrice>0)&(params.options>0))
        
        self.data.contractBuyer[sp.sender] = sp.record(strikePrice = params.strikePrice, pool = sp.map(),adminpayment =sp.nat(0),options=params.options)
        

    @sp.entry_point
    def putSeller(self,params):
        sp.verify(params.amount >= 10000 )
        sp.if self.data.liquidityPool.contains(sp.sender):
            self.data.liquidityPool[sp.sender].amount += params.amount
        sp.else: 
            self.data.liquidityPool[sp.sender] = sp.record(amount=params.amount,premium=sp.nat(0))
        self.data.totalLiquidity += params.amount
    
    @sp.entry_point
    def modifyPrice(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.xtzPrice = params.price

@sp.add_test(name = "Put Contract Testing")
def test():
    
    admin = sp.address("tz123")
    alice = sp.address("tz1456")
    bob   = sp.address("tz1678")

    scenario = sp.test_scenario()
    c1 = PutContract(admin,100)
    scenario += c1
    
    scenario += c1.putBuyer(strikePrice=100,options=5).run(sender=alice)
    
    scenario += c1.modifyPrice(price=100).run(sender=admin)
    
    scenario += c1.putSeller(amount=50000).run(sender=bob)
    scenario += c1.putSeller(amount=10000).run(sender=bob)