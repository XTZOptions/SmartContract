import smartpy as sp

class PutContract(sp.Contract):
    def __init__(self,admin,end_date):

        self.init(contractBuyer=sp.map(),liquidityPool=sp.map(),administrator = admin,
        totalLiquidity=sp.nat(0),end_date=sp.timestamp(end_date),
        xtzPrice=300,adminAccount=100000)

    @sp.entry_point
    def putBuyer(self, params):

        sp.verify(~self.data.contractBuyer.contains(sp.sender))
        sp.verify((params.strikePrice>0)&(params.options>0)&(params.fee > 0))

        totalAmount = params.strikePrice*params.options*100
        sp.verify(self.data.totalLiquidity > totalAmount)
        
        self.data.contractBuyer[sp.sender] = sp.record(strikePrice = params.strikePrice, pool = sp.map(),adminpayment =sp.nat(0),options=params.options)
        
       
        premiumCal = 0  
        CollateralCal = 0 
        sp.for i in self.data.liquidityPool.keys():
            premiumCal = self.data.liquidityPool[i].amount*params.fee 
            premiumCal = premiumCal/self.data.totalLiquidity
            self.data.liquidityPool[i].premium += premiumCal
            
            CollateralCal = self.data.liquidityPool[i].amount*params.strikePrice*params.options
            CollateralCal = CollateralCal/self.data.totalLiquidity
            self.data.contractBuyer[sp.sender].pool[i] = CollateralCal
        
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
    # Put Buyers
    alice = sp.address("tz1456")
    # Put Sellers
    bob   = sp.address("tz1678")
    alex = sp.address("tz1910")

    scenario = sp.test_scenario()
    c1 = PutContract(admin,100)
    scenario += c1

    scenario += c1.putSeller(amount=50000).run(sender=bob)
    scenario += c1.putSeller(amount=10000).run(sender=bob)
    scenario += c1.putSeller(amount=10000).run(sender=alex)
    
    scenario += c1.putBuyer(strikePrice=100,options=5,fee=100).run(sender=alice)
    
    scenario += c1.modifyPrice(price=100).run(sender=admin)
    
    