    import smartpy as sp

    class PutOptions(sp.Contract):

        def __init__(self,admin,endCycle,endWithdraw):

            self.init(contractBuyer= sp.big_map(),contractSellar = sp.big_map(),
            administrator = admin,buyerSet = sp.set(),poolSet=sp.set(),
                xtzPrice=300,validation=sp.record(cycleEnd=sp.timestamp(endCycle),withdrawTime=sp.timestamp(endWithdraw),totalSupply=sp.nat(0)),
                tokenContract=sp.none
            )


        @sp.entry_point
        def putBuyer(self,params):

            sp.verify(sp.now < self.data.validation.cycleEnd)
            sp.verify(~ self.data.contractBuyer.contains(sp.sender))
        
            self.data.buyerSet.add(sp.sender)
            value = sp.now.add_hours(5)

            TotalAmount = sp.local('TotalAmount',params.strikePrice*params.options)
            CollateralTotal = sp.local('CollateralTotal',0)

            self.data.contractBuyer[sp.sender] = sp.record(strikePrice = params.strikePrice, pool = sp.map(),adminpayment =0,options=params.options,
            expiry=value)

            sp.for i in self.data.poolSet.elements():
                self.data.contractBuyer[sp.sender].pool[i] = (self.data.contractSellar[i].amount*TotalAmount.value)/self.data.validation.totalSupply 
                
                CollateralTotal.value += self.data.contractBuyer[sp.sender].pool[i]

                self.data.contractSellar[i].amount = abs(self.data.contractSellar[i].amount - (self.data.contractSellar[i].amount*TotalAmount.value)/self.data.validation.totalSupply)

            sp.if CollateralTotal.value !=  params.strikePrice*params.options : 
                self.data.contractBuyer[sp.sender].adminpayment = params.strikePrice*params.options - CollateralTotal.value
                self.data.validation.totalSupply = abs(self.data.validation.totalSupply - CollateralTotal.value)

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
        def sellPut(self):
            sp.verify(sp.now < self.data.validation.cycleEnd)
            sp.verify(self.data.contractBuyer.contains(sp.sender))

            sp.verify(sp.now < self.data.contractBuyer[sp.sender].expiry)

            sp.if self.data.contractBuyer[sp.sender].strikePrice > self.data.xtzPrice:  
                # Pass amount to the token amount 
                #c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TInt), self.data.tokenContract, entry_point = "LockToken").open_some()
                #mydata = sp.record(address = sp.sender,amount=params.amount)
                #sp.transfer(mydata, sp.mutez(0), c)
                self.data.buyerSet.remove(sp.sender)
                del self.data.contractBuyer[sp.sender]

        @sp.entry_point
        def ResetContract(self):
            
            sp.verify(sp.sender == self.data.administrator)
            sp.verify(sp.now >  self.data.validation.cycleEnd)

            sp.for i in self.data.buyerSet.elements():

                sp.if self.data.xtzPrice < self.data.contractBuyer[i].strikePrice: 

                    # Pass amount to the token amount 
                    #c = sp.contract(sp.TRecord(address = sp.TAddress, amount = sp.TInt), self.data.tokenContract, entry_point = "LockToken").open_some()
                    #mydata = sp.record(address = sp.sender,amount=params.amount)
                    #sp.transfer(mydata, sp.mutez(0), c)
                    self.data.buyerSet.remove(i)
                    del self.data.contractBuyer[i]

                sp.else: 

                    sp.for j in self.data.contractBuyer[i].pool.keys():
                        self.data.contractSellar[j].amount += self.data.contractBuyer[i].pool[j]
                        

                    self.data.buyerSet.remove(i)
                    del self.data.contractBuyer[i]
                    
                    self.data.adminpayment


        @sp.entry_point
        def ModifyPrice(self,params):
            sp.verify(sp.sender == self.data.administrator)
            self.data.xtzPrice = params.price

    @sp.add_test(name = "Put Contract Testing")
    def test():
        
        admin = sp.address("tz123")
        # Put Buyers    
        bob   = sp.address("tz1678")
        
        # Put Sellers
        alice = sp.address("tz1456")
        alex = sp.address("tz1910")

        scenario = sp.test_scenario()
        c1 =  PutOptions(admin,100,120)
        scenario += c1

        scenario += c1.putSeller(amount=50000).run(now=45,sender=alice)
        scenario += c1.putSeller(amount=10000).run(now=45,sender=alice)
        scenario += c1.putSeller(amount=10000).run(now=45,sender=alex)
        
        scenario += c1.putBuyer(strikePrice=10,options=5,expiry=65).run(now=50,sender=bob)
