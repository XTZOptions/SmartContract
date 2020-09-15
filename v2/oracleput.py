import smartpy as sp

class XTZOracle(sp.Contract):
    def __init__(self, admin):
        
        self.init(xtzPrice = sp.nat(0), keysset = sp.set([admin]) , owner = admin,StrikePrice=sp.map())
    
    @sp.entry_point
    def feedData(self,params):
        sp.if (self.data.keysset.contains(sp.sender)):
            self.data.xtzPrice = params.price 
            
    @sp.entry_point
    def feedStrike(self,params):
        sp.if (self.data.keysset.contains(sp.sender)):
            self.data.StrikePrice[80] = params.one
            self.data.StrikePrice[90] = params.two
            self.data.StrikePrice[100] = params.three
            self.data.StrikePrice[110] = params.four
            self.data.StrikePrice[120] = params.five
            self.data.xtzPrice = params.three

    @sp.entry_point
    def GetputSeller(self,params):
        
        price = sp.set([80,90,100,110,120])
        duration = sp.set([7,14,21])

        sp.verify(params.Options>0)
        sp.verify(price.contains(params.Ratio))
        sp.verify(duration.contains(params.expire))

        data = sp.record(Options=params.Options,Ratio=params.Ratio,StrikePrice=self.data.StrikePrice[params.Ratio],
        address=params.address,expire=params.expire,xtzPrice=self.data.xtzPrice)

        contract = sp.contract(sp.TRecord(Options=sp.TNat,Ratio=sp.TInt,StrikePrice=sp.TNat,address = sp.TAddress,
        expire = sp.TInt,xtzPrice=sp.TNat),sp.sender,entry_point = "OrOputBuyer").open_some()

        
        sp.if sp.amount == sp.mutez(10):
            sp.transfer(data,sp.mutez(0),contract)
        sp.else:
            sp.transfer(data,sp.amount,contract)

    @sp.entry_point
    def addDataContributor(self,params):
        sp.if sp.sender == self.data.owner:
            self.data.keysset.add(params.contributor)
    
    @sp.entry_point
    def getDataMint(self,params):
    
        data = sp.record(price=sp.to_int(self.data.xtzPrice),address=params.address,amount=params.amount)
        
        contract = sp.contract(sp.TRecord( price = sp.TInt,address = sp.TAddress, amount = sp.TInt),sp.sender,entry_point = "OrOMint").open_some()
        
        sp.if sp.amount == sp.mutez(10):
            sp.transfer(data,sp.mutez(0),contract)
        sp.else:
            sp.transfer(data,sp.amount,contract)

class PutOptions(sp.Contract):

    def __init__(self,admin,endCycle,endWithdraw,token,oro):

        self.init(contractBuyer= sp.big_map(),contractSellar = sp.big_map(),
        administrator = admin,buyerSet = sp.set(),poolSet=sp.set(),
           validation=sp.record(cycleEnd=sp.timestamp(endCycle),withdrawTime=sp.timestamp(endWithdraw),totalSupply=sp.nat(0)),
            tokenContract=token,adminAccount=0,model=sp.map(),Oracle=oro)


    @sp.entry_point
    def putBuyer(self,params):

        sp.verify(sp.now < self.data.validation.cycleEnd)
        sp.verify(~ self.data.contractBuyer.contains(sp.sender))
        
        price = sp.set([80,90,100,110,120])
        duration = sp.set([7,14,21])
        
        sp.verify(price.contains(params.StrikePrice))
        sp.verify(params.Options>0)
        sp.verify(duration.contains(sp.to_int(params.expire)))
        
        sp.verify(self.data.validation.cycleEnd > sp.now.add_days(sp.to_int(params.expire)))

        data = sp.record(Options=abs(params.Options),Ratio=sp.to_int(params.StrikePrice),address=sp.sender,expire=sp.to_int(params.expire))
        
        contract = sp.contract(sp.TRecord(Options = sp.TNat,address = sp.TAddress,Ratio = sp.TInt,expire=sp.TInt),self.data.Oracle,entry_point = "GetputSeller").open_some()
        #Oracle Call

        sp.transfer(data, sp.mutez(10), contract)


    @sp.entry_point
    def OrOputBuyer(self,params):

        # Verify Oracle Address
        sp.verify(sp.sender == self.data.Oracle)

        sp.verify(sp.now < self.data.validation.cycleEnd)
        sp.verify(~ self.data.contractBuyer.contains(params.address))

        self.data.model[80] = {7:1,14:2,21:4}
        self.data.model[90] = {7:2,14:4,21:8}
        self.data.model[100] = {7:4,14:8,21:16}
        self.data.model[110] = {7:2,14:4,21:8}
        self.data.model[120] = {7:1,14:2,21:4}

        sp.verify(self.data.model.contains(params.Ratio))

        sp.verify(self.data.model[params.Ratio].contains(params.expire))
        
        TotalAmount = sp.local('TotalAmount',params.StrikePrice*params.Options*100)

        Interest = sp.local('Interest',self.data.model[params.Ratio][params.expire])
        
        del self.data.model[80]
        del self.data.model[90]
        del self.data.model[100]
        del self.data.model[110]
        del self.data.model[120]
        
        
        Deadline = sp.now.add_days(params.expire)


        sp.verify(self.data.validation.totalSupply > TotalAmount.value)
        sp.verify(self.data.validation.cycleEnd > sp.now.add_days(params.expire))
        

        self.data.adminAccount += params.StrikePrice*params.Options
        self.data.buyerSet.add(sp.sender)

        
        CollateralTotal = sp.local('CollateralTotal',0)


        PremiumCal =  sp.local('PremiumCal',params.StrikePrice*params.Options*Interest.value)
        
        Payment = sp.local('Payment',params.StrikePrice*params.Options*Interest.value + params.StrikePrice*params.Options)
        

        sp.if params.StrikePrice > params.xtzPrice: 
            PremiumCal.value += abs((params.StrikePrice - params.xtzPrice)*100)
            Payment.value += abs((params.StrikePrice - params.xtzPrice)*100)

        self.Lock(params.address,Payment.value)
        PremiumTotal = sp.local('PremiumTotal',0)
       
        self.data.contractBuyer[params.address] = sp.record(strikePrice = params.StrikePrice, pool = sp.map(),adminpayment =0,options=params.Options,
        expiry=Deadline)

        sp.for i in self.data.poolSet.elements():
            self.data.contractBuyer[params.address].pool[i] = (self.data.contractSellar[i].amount*TotalAmount.value)/self.data.validation.totalSupply 
            
            CollateralTotal.value += self.data.contractBuyer[params.address].pool[i]
            
            self.data.contractSellar[i].premium += (self.data.contractSellar[i].amount*PremiumCal.value)/self.data.validation.totalSupply 
            PremiumTotal.value += (self.data.contractSellar[i].amount*PremiumCal.value)/self.data.validation.totalSupply 
            
            self.data.contractSellar[i].amount = abs(self.data.contractSellar[i].amount - (self.data.contractSellar[i].amount*TotalAmount.value)/self.data.validation.totalSupply)
            
            
        self.data.adminAccount += abs(PremiumCal.value - PremiumTotal.value)
        self.data.validation.totalSupply = abs(self.data.validation.totalSupply - CollateralTotal.value)

        sp.if CollateralTotal.value !=  params.StrikePrice*params.Options*100: 
            self.data.contractBuyer[params.address].adminpayment = abs(params.StrikePrice*params.Options*100 - CollateralTotal.value)
            self.data.adminAccount = abs(self.data.adminAccount - self.data.contractBuyer[params.address].adminpayment)
            

    @sp.entry_point
    def putSeller(self,params):
        
        sp.verify(sp.now < self.data.validation.cycleEnd)
        sp.verify(params.amount >= 10000)
        sp.verify(params.amount %10000 == 0 )
        # Token Contract Call 

        self.Lock(sp.sender,params.amount)

        sp.if self.data.poolSet.contains(sp.sender):

            self.data.contractSellar[sp.sender].amount += params.amount

        sp.else:

            self.data.poolSet.add(sp.sender) 

            self.data.contractSellar[sp.sender] = sp.record(amount=0,premium=0)
            self.data.contractSellar[sp.sender].amount += params.amount

        self.data.validation.totalSupply += params.amount
            
    
    @sp.entry_point
    def ReleaseContract(self,params):
        
        sp.verify(sp.now < self.data.validation.cycleEnd)
        sp.verify(self.data.contractBuyer.contains(params.address))

        sp.verify(sp.now < self.data.contractBuyer[params.address].expiry)
        
        sp.if self.data.contractBuyer[params.address].strikePrice > params.xtzPrice:  
           
            self.data.adminAccount += self.data.contractBuyer[params.address].adminpayment
            Amount = sp.local('Amount',(self.data.contractBuyer[params.address].strikePrice - params.xtzPrice)*100)
            PoolAmount = sp.local('PoolAmount',(self.data.contractBuyer[params.address].strikePrice*self.data.contractBuyer[params.address].options)*100 - self.data.contractBuyer[params.address].adminpayment)

            TotalCal =  sp.local('TotalCal',0)

            sp.for i in  self.data.contractBuyer[params.address].pool.keys():
                TotalCal.value += (self.data.contractBuyer[params.address].pool[i]*abs(Amount.value))/abs(PoolAmount.value)
                self.data.contractBuyer[params.address].pool[i] = abs(self.data.contractBuyer[params.address].pool[i] - (self.data.contractBuyer[params.address].pool[i]*abs(Amount.value))/abs(PoolAmount.value)) 
            
                self.data.contractSellar[i].amount += self.data.contractBuyer[params.address].pool[i]

            sp.if  TotalCal.value != abs(Amount.value): 
                self.data.adminAccount = abs( self.data.adminAccount - abs(abs(Amount.value) - TotalCal.value)) 

            
            self.Unlock(params.address,abs(Amount.value))
            self.data.buyerSet.remove(params.address)
            del self.data.contractBuyer[params.address]

    @sp.entry_point
    def ResetContract(self):
        
        sp.for i in self.data.buyerSet.elements():

            sp.if sp.now > self.data.contractBuyer[i].expiry: 
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

        Payment = sp.local('Payment',self.data.contractSellar[sp.sender].premium + self.data.contractSellar[sp.sender].amount)
        
        self.Unlock(sp.sender,Payment.value)

        self.data.poolSet.remove(sp.sender)
        del self.data.contractSellar[sp.sender]

    @sp.entry_point
    def WithdrawPremium(self,params):
        sp.verify(self.data.contractSellar.contains(sp.sender))
        sp.verify(self.data.contractSellar[sp.sender].premium > 0 )

        self.Unlock(sp.sender,self.data.contractSellar[sp.sender].premium)
        self.data.contractSellar[sp.sender].premium  = 0


    def Lock(self,address,amount):
        c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TNat), self.data.tokenContract, entry_point = "LockToken").open_some()
        mydata = sp.record(address = address,amount=amount)
        sp.transfer(mydata, sp.mutez(0), c)
    
    def Unlock(self,address,amount):
        c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TNat), self.data.tokenContract, entry_point = "UnlockToken").open_some()
        mydata = sp.record(address = address,amount=amount)
        sp.transfer(mydata, sp.mutez(0), c)


    @sp.entry_point
    def RestartCycle(self):
        sp.verify(sp.sender == self.data.administrator)
        sp.verify(sp.now > self.data.validation.withdrawTime)

        self.data.validation.cycleEnd = sp.now.add_days(23)
        self.data.validation.withdrawTime = sp.now.add_days(25)

    
@sp.add_test(name="XTZOracle Testing")
def test():
    scenario = sp.test_scenario()
    
    admin = sp.test_account("Alice")
    alice = sp.test_account("Alice")
    bob   = sp.test_account("Robert")
    alex = sp.test_account("Alex")
    token = sp.address("KT1KtyJeL78tdHnzwCPE8M14WDb1zqsnLkjQ")

    oracle = XTZOracle(admin.address)
    scenario += oracle

    c1 =  PutOptions(admin.address,10,20,token,oracle.address)
    scenario += c1 

    scenario += oracle.feedData(price=400).run(sender=admin)
    scenario += oracle.feedData(price=600).run(sender=admin)

    
    
    scenario += oracle.feedStrike(one=320,two=360,three=400,four=440,five=480).run(sender=admin)
    scenario += oracle.GetputSeller(Options=1,Ratio=80,address=admin.address,expire=14).run(sender=admin)
    
    scenario += c1.RestartCycle().run(sender=admin,now=30)
    
    scenario += c1.putSeller(amount=50000).run(now=45,sender=alice,amount=sp.tez(100000))
    scenario += c1.putSeller(amount=10000).run(now=45,sender=alice)
    scenario += c1.putSeller(amount=10000).run(now=45,sender=alex)

    scenario += c1.putBuyer(Options=1,StrikePrice=100,expire=7).run(sender=bob)
    #scenario += oracle.getDataMint(address=alice.address,amount=10).run(sender=alice)