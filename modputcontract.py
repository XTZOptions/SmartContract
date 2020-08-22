import smartpy as sp

class PutContract(sp.Contract):
    def __init__(self,admin,endCycle,endWithdraw):

        self.init(contractBuyer=sp.big_map(),liquidityPool=sp.big_map(),poolMap = sp.big_map(),
        administrator = admin,poolCounter=0,
        totalLiquidity=0,xtzPrice=300,adminAccount=100000,tempcal=0,
        cycleEnd=sp.timestamp(endCycle),withdrawTime=sp.timestamp(endWithdraw))

    @sp.entry_point
    def putBuyer(self,params):
        
        sp.verify(sp.now < self.data.cycleEnd)
        sp.verify(~self.data.contractBuyer.contains(sp.sender))

        totalAmount = params.strikePrice*params.options*100
        sp.verify(self.data.totalLiquidity > totalAmount)

        self.data.contractBuyer[sp.sender] = sp.record(strikePrice = params.strikePrice, pool = sp.map(),adminpayment =0,options=params.options)


    
    @sp.entry_point
    def putSeller(self,params):
        sp.verify(sp.now < self.data.cycleEnd)

        sp.if self.data.poolMap.contains(sp.sender):

            self.data.liquidityPool[self.data.poolMap[sp.sender]].amount += params.amount
        
        sp.else: 

            self.data.poolMap[sp.sender] = self.data.poolCounter 
            self.data.liquidityPool[self.data.poolCounter] = sp.record(amount=0,premium=0,address=sp.sender)
            self.data.liquidityPool[self.data.poolCounter].amount += params.amount
            self.data.poolCounter += 1 

        self.data.totalLiquidity += params.amount


@sp.add_test(name = "Put Contract Testing")
def test():
    
    admin = sp.address("tz123")
    # Put Buyers    
    bob   = sp.address("tz1678")
    
    # Put Sellers
    alice = sp.address("tz1456")
    alex = sp.address("tz1910")

    scenario = sp.test_scenario()
    c1 = PutContract(admin,100,120)
    scenario += c1
    scenario += c1.putSeller(amount=50000).run(now=45,sender=alex)
    scenario += c1.putSeller(amount=10000).run(now=46,sender=alex)

    scenario += c1.putSeller(amount=40000).run(now=47,sender=alice)

    scenario += c1.putBuyer().run(now=50,sender=bob)

    # scenario += c1.putBuyer().run(now=50)
