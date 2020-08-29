import smartpy as sp

class PutOptions(sp.Contract):

    def __init__(self,admin,endCycle,endWithdraw,token):

        self.init(contractBuyer= sp.big_map(),contractSellar = sp.big_map(),
        administrator = admin,buyerSet = sp.set(),poolSet=sp.set(),
            xtzPrice=400,validation=sp.record(cycleEnd=sp.timestamp(endCycle),withdrawTime=sp.timestamp(endWithdraw),totalSupply=sp.nat(0)),
            tokenContract=token,adminAccount=0,model = sp.map()
        )


    @sp.entry_point
    def putBuyer(self,params):

        sp.verify(sp.now < self.data.validation.cycleEnd)
        sp.verify(~ self.data.contractBuyer.contains(sp.sender))
        
        self.data.model[self.data.xtzPrice*90] = {7:1,14:2,21:4}
        self.data.model[self.data.xtzPrice*95] = {7:2,14:4,21:8}
        self.data.model[self.data.xtzPrice*100] = {7:4,14:8,21:16}
        self.data.model[self.data.xtzPrice*105] = {7:2,14:4,21:8}
        self.data.model[self.data.xtzPrice*110] = {7:1,14:2,21:4}

        sp.verify(self.data.model.contains(params.StrikePrice*100))
        sp.verify(self.data.model[params.StrikePrice*100].contains(params.expire))
        
        TotalAmount = sp.local('TotalAmount',params.StrikePrice*params.Options*100)

        Interest = sp.local('Interest',self.data.model[params.StrikePrice*100][params.expire])
        
        Deadline = sp.now.add_days(params.expire)
        
        # Transfer Token to the Contract 


        # Deleting Pricing Model 
        del self.data.model[self.data.xtzPrice*90]
        del self.data.model[self.data.xtzPrice*95]
        del self.data.model[self.data.xtzPrice*100]
        del self.data.model[self.data.xtzPrice*105]
        del self.data.model[self.data.xtzPrice*110]
        


        self.data.adminAccount += params.StrikePrice*params.Options
        self.data.buyerSet.add(sp.sender)

        
        CollateralTotal = sp.local('CollateralTotal',0)


        PremiumCal =  sp.local('PremiumCal',params.StrikePrice*params.Options*Interest.value)
        
        sp.if params.StrikePrice > self.data.xtzPrice: 
            PremiumCal.value += abs((params.StrikePrice - self.data.xtzPrice)*100)

        PremiumTotal = sp.local('PremiumTotal',0)
        sp.send(sp.sender,sp.tez(PremiumCal.value))
        self.data.contractBuyer[sp.sender] = sp.record(strikePrice = params.StrikePrice, pool = sp.map(),adminpayment =0,options=params.Options,
        expiry=Deadline)

        sp.for i in self.data.poolSet.elements():
            self.data.contractBuyer[sp.sender].pool[i] = (self.data.contractSellar[i].amount*TotalAmount.value)/self.data.validation.totalSupply 
            
            CollateralTotal.value += self.data.contractBuyer[sp.sender].pool[i]
            
            self.data.contractSellar[i].premium += (self.data.contractSellar[i].amount*PremiumCal.value)/self.data.validation.totalSupply 
            PremiumTotal.value += (self.data.contractSellar[i].amount*PremiumCal.value)/self.data.validation.totalSupply 
            
            self.data.contractSellar[i].amount = abs(self.data.contractSellar[i].amount - (self.data.contractSellar[i].amount*TotalAmount.value)/self.data.validation.totalSupply)
            
            
        self.data.adminAccount += abs(PremiumCal.value - PremiumTotal.value)
        self.data.validation.totalSupply = abs(self.data.validation.totalSupply - CollateralTotal.value)

        sp.if CollateralTotal.value !=  params.StrikePrice*params.Options*100: 
            self.data.contractBuyer[sp.sender].adminpayment = abs(params.StrikePrice*params.Options*100 - CollateralTotal.value)
            self.data.adminAccount = abs(self.data.adminAccount - self.data.contractBuyer[sp.sender].adminpayment)
            

    @sp.entry_point
    def putSeller(self,params):
        
        sp.verify(sp.now < self.data.validation.cycleEnd)
        sp.verify(params.amount >= 10000)
        sp.verify(params.amount %10000 == 0 )
        # Token Contract Call 

        #c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TInt), self.data.tokenContract, entry_point = "LockToken").open_some()
        #mydata = sp.record(address = sp.sender,amount=params.amount)
        #sp.transfer(mydata, sp.mutez(0), c)

        sp.if self.data.poolSet.contains(sp.sender):

            self.data.contractSellar[sp.sender].amount += params.amount

        sp.else:

            self.data.poolSet.add(sp.sender) 

            self.data.contractSellar[sp.sender] = sp.record(amount=0,premium=0)
            self.data.contractSellar[sp.sender].amount += params.amount

        self.data.validation.totalSupply += params.amount
            
    @sp.entry_point
    def ReleaseContract(self):
        
        sp.verify(sp.now < self.data.validation.cycleEnd)
        sp.verify(self.data.contractBuyer.contains(sp.sender))

        sp.verify(sp.now < self.data.contractBuyer[sp.sender].expiry)

        sp.if self.data.contractBuyer[sp.sender].strikePrice > self.data.xtzPrice:  
            # Pass amount to the token amount 
            #c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TInt), self.data.tokenContract, entry_point = "UnlockToken").open_some()
            #mydata = sp.record(address = sp.sender,amount=params.amount)
            #sp.transfer(mydata, sp.mutez(0), c)

            Amount = sp.local('Amount',(self.data.contractBuyer[sp.sender].strikePrice - self.data.xtzPrice)*100)
            PoolAmount = sp.local('PoolAmount',(self.data.contractBuyer[sp.sender].strikePrice*self.data.contractBuyer[sp.sender].options)*100 - self.data.contractBuyer[sp.sender].adminpayment)

            sp.for i in  self.data.contractBuyer[sp.sender].pool.keys():
                pass


            self.data.buyerSet.remove(sp.sender)
            del self.data.contractBuyer[sp.sender]

    @sp.entry_point
    def ResetContract(self):
        
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(sp.now >  self.data.validation.cycleEnd)

        sp.for i in self.data.buyerSet.elements():

            sp.for j in self.data.contractBuyer[i].pool.keys():
                self.data.contractSellar[j].amount += self.data.contractBuyer[i].pool[j]
                
            self.data.adminAccount += self.data.contractBuyer[i].adminpayment
            self.data.buyerSet.remove(i)
            del self.data.contractBuyer[i]
            
            
    @sp.entry_point
    def WithdrawToken(self,params):
        
        sp.verify(sp.now > self.data.validation.cycleEnd)
        sp.verify(sp.now < self.data.validation.withdrawTime)
        sp.verify(self.data.contractSellar.contains(sp.sender))

        # Pass amount to the token amount 
        #c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TInt), self.data.tokenContract, entry_point = "UnlockToken").open_some()
        #mydata = sp.record(address = sp.sender,amount=params.amount)
        #sp.transfer(mydata, sp.mutez(0), c)
        self.data.poolSet.remove(sp.sender)
        del self.data.contractSellar[sp.sender]



    @sp.entry_point
    def ModifyPrice(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.xtzPrice = params.price

@sp.add_test(name = "Put Contract Testing")
def test():
    
    admin = sp.address("tz1hPnEdcKWrdeZEAQiGfmV6knHA5En1fCwQ")
    # Put Buyers    
    token = sp.address("KT1XKqN7zAKHTYa8ck36Gc8ti4PeRKWa9v8P")
    bob   = sp.address("tz1678")
    
    # Put Sellers
    alice = sp.address("tz1456")
    alex = sp.address("tz1910")

    scenario = sp.test_scenario()
    c1 =  PutOptions(admin,100,120,token)
    scenario += c1

    scenario += c1.putSeller(amount=50000).run(now=45,sender=alice,amount=sp.tez(10000))
    scenario += c1.putSeller(amount=10000).run(now=45,sender=alice)
    scenario += c1.putSeller(amount=10000).run(now=45,sender=alex)
    
    scenario += c1.putBuyer(StrikePrice=360,Options=1,expire=14).run(now=50,sender=bob)
