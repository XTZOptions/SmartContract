import smartpy as sp

class PutContract(sp.Contract):
    def __init__(self,admin,end_date):

        self.init(contractBuyer=sp.map(),liquidityPool=sp.map(),administrator = admin,
        totalLiquidity=0,end_date=sp.timestamp(end_date),
        xtzPrice=300,adminAccount=100000,tempcal=0)

    @sp.entry_point
    def putBuyer(self, params):

        sp.verify(~self.data.contractBuyer.contains(sp.sender))
        sp.verify((params.strikePrice>0)&(params.options>0)&(params.fee > 0))

        totalAmount = params.strikePrice*params.options*100
        sp.verify(self.data.totalLiquidity > totalAmount)
        
        self.data.contractBuyer[sp.sender] = sp.record(strikePrice = sp.to_int(params.strikePrice), pool = sp.map(),adminpayment =0,options=sp.to_int(params.options))
        
       
        premiumCal = 0  
        CollateralCal = 0 
        self.data.tempcal = 0 
        sp.for i in self.data.liquidityPool.keys():
            premiumCal = self.data.liquidityPool[i].amount*params.fee 
            premiumCal = premiumCal/self.data.totalLiquidity
            self.data.liquidityPool[i].premium += premiumCal
            
            CollateralCal = self.data.liquidityPool[i].amount*params.strikePrice*params.options*100
            CollateralCal = CollateralCal/self.data.totalLiquidity
            
            self.data.contractBuyer[sp.sender].pool[i] = CollateralCal
            self.data.liquidityPool[i] -= self.data.contractBuyer[sp.sender].pool[i]
            self.data.tempcal += CollateralCal
        
        self.data.totalLiquidity -= self.data.tempcal
        
    @sp.entry_point
    def putSeller(self,params):
        sp.verify(params.amount >= 10000 )
        
        sp.if self.data.liquidityPool.contains(sp.sender):
            self.data.liquidityPool[sp.sender].amount += params.amount
        sp.else: 
            self.data.liquidityPool[sp.sender] = sp.record(amount=0,premium=0)
            self.data.liquidityPool[sp.sender].amount += params.amount
        self.data.totalLiquidity += params.amount
    

    @sp.entry_point
    def sellContract(self,params):
        sp.verify(self.data.contractBuyer.contains(sp.sender))
        sp.if self.data.contractBuyer[sp.sender].strikePrice > self.data.xtzPrice :
            pass
            # Transfer StrikePrice*Options*100 into account
        sp.else: 
            sp.for i in  self.data.contractBuyer[sp.sender].pool.keys():
                self.data.liquidityPool[i].amount += self.data.contractBuyer[sp.sender].pool[i]
    
    @sp.entry_point
    def resetContract(self,params):
        # Add time verification case before deployment 
        sp.verify(sp.sender == self.data.administrator)
        sp.for i in self.data.contractBuyer.keys():
            sp.if self.data.contractBuyer[i].strikePrice > self.data.xtzPrice:
                pass
                # External Contract Call to transfer amount
            sp.else:
                sp.for j in  self.data.contractBuyer[i].pool.keys():
                    self.data.liquidityPool[j].amount += self.data.contractBuyer[i].pool[j]
    
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

    scenario += c1.putSeller(amount=50000).run(sender=alice)
    scenario += c1.putSeller(amount=10000).run(sender=alice)
    scenario += c1.putSeller(amount=10000).run(sender=alex)
    
    scenario += c1.putBuyer(strikePrice=100,options=5,fee=100).run(sender=bob)
    
    # scenario += c1.modifyPrice(price=100).run(sender=admin)
    # scenario += c1.resetContract().run(sender=admin)
    