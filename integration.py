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
        self.addAddressIfNecessary(params.address)
        self.data.ledger[params.address].balance += abs(self.data.xtzPrice*params.value*100)
        self.data.totalSupply += abs(self.data.xtzPrice*params.value*100)

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
        
        Payment = sp.local('Payment',params.StrikePrice*params.Options*Interest.value + params.StrikePrice*params.Options)
        self.Lock(sp.sender,Payment.value)

        sp.if params.StrikePrice > self.data.xtzPrice: 
            PremiumCal.value += abs((params.StrikePrice - self.data.xtzPrice)*100)

        PremiumTotal = sp.local('PremiumTotal',0)
       
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

        self.Lock(sp.sender,params.amount)

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
            self.data.adminAccount += self.data.contractBuyer[sp.sender].adminpayment
            Amount = sp.local('Amount',(self.data.contractBuyer[sp.sender].strikePrice - self.data.xtzPrice)*100)
            PoolAmount = sp.local('PoolAmount',(self.data.contractBuyer[sp.sender].strikePrice*self.data.contractBuyer[sp.sender].options)*100 - self.data.contractBuyer[sp.sender].adminpayment)

            TotalCal =  sp.local('TotalCal',0)

            sp.for i in  self.data.contractBuyer[sp.sender].pool.keys():
                TotalCal.value += (self.data.contractBuyer[sp.sender].pool[i]*abs(Amount.value))/abs(PoolAmount.value)
                self.data.contractBuyer[sp.sender].pool[i] = abs(self.data.contractBuyer[sp.sender].pool[i] - (self.data.contractBuyer[sp.sender].pool[i]*abs(Amount.value))/abs(PoolAmount.value)) 
            
                self.data.contractSellar[i].amount += self.data.contractBuyer[sp.sender].pool[i]

            sp.if  TotalCal.value != abs(Amount.value): 
                self.data.adminAccount = abs( self.data.adminAccount - abs(abs(Amount.value) - TotalCal.value)) 

            sp.send(sp.sender,sp.tez(abs(Amount.value)))
            self.Unlock(sp.sender,abs(Amount.value))
            self.data.buyerSet.remove(sp.sender)
            del self.data.contractBuyer[sp.sender]

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
    def ModifyPrice(self,params):
        sp.verify(sp.sender == self.data.administrator)
        self.data.xtzPrice = params.price

@sp.add_test(name = "ALA Token")
def test():

    scenario = sp.test_scenario()
    
    admin = sp.address("tz1LAWQmxJcnK43vR9G8jsNTzR6b2unZ58NX")
    alice = sp.test_account("Alice")
    bob   = sp.test_account("Robert")
    alex = sp.test_account("Alex")

    c1 = ALAToken(admin)
    c2 = PutOptions(admin,100,120,c1.address)
    
    scenario += c1
    scenario += c2
    
    scenario += c1.AddContract(c2.address).run(sender=admin)
    scenario += c1.mint(address = alice.address, value = 2).run(sender = alice,amount = sp.tez(2))

    scenario += c2.putSeller(amount=50000).run(now=45,sender=alice,amount=sp.tez(100000))
    
    scenario += c1.mint(address = bob.address, value = 1).run(sender = bob,amount = sp.tez(1))

    scenario += c2.putBuyer(StrikePrice=400,Options=1,expire=14).run(now=50,sender=bob)
    scenario += c2.WithdrawPremium().run(sender=alice)
    # scenario += c2.ModifyPrice(price=300).run(sender=admin)
    # scenario += c2.ReleaseContract().run(sender=bob)