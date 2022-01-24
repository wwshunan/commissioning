import importlib

class Test(object):
    def __init__(self, module, userCodeId):
        mod = importlib.import_module(module)
        userCode = getattr(mod, userCodeId)
        self.userCode = None
        self.setUserCode(userCode)

    def setUserCode(self, userCode):
        self.userCode = userCode

    def execUserCode(self):
        self.userCode()

A = Test('user_codes.user_codes', 'A')
A.execUserCode()
B = Test('user_codes.user_codes', 'B')
B.execUserCode()
