import smartpy as sp

class PutContract(sp.Contract):
    def __init__(self):
        self.init(val=sp.big_map())

    @sp.entry_point
    def enter(self, params):
        sp.verify(~self.data.val.contains(sp.sender))
        self.data.val[sp.sender] = 123
        

@sp.add_test(name = "Minimal")
def test():
    
    admin = sp.address("tz123")
    alice = sp.address("tz1456")
    bob   = sp.address("tz1678")

    scenario = sp.test_scenario()
    c1 = PutContract()
    scenario += c1
    scenario += c1.enter().run(sender=alice,amount=sp.tez(1))