import smartpy as sp

class PutContract(sp.Contract):
    def __init__(self,admin):
        self.init(contractBuyer=sp.big_map(),liquidityPool=sp.big_map(),administrator = admin,
        PoolWriters=sp.nat(0),totalLiquidity=sp.nat(0))

    @sp.entry_point
    def putBuyer(self, params):
        sp.verify(~self.data.contractBuyer.contains(sp.sender))
        self.data.contractBuyer[sp.sender] = sp.record(strikePrice = params.strikePrice, pool = sp.map(),adminpayment =sp.nat(0))
        

    @sp.entry_point
    def putSeller(self,params):
        pass


@sp.add_test(name = "Put Contract Testing")
def test():
    
    admin = sp.address("tz123")
    alice = sp.address("tz1456")
    bob   = sp.address("tz1678")

    scenario = sp.test_scenario()
    c1 = PutContract(admin)
    scenario += c1
    scenario += c1.putBuyer(strikePrice=100).run(sender=alice)