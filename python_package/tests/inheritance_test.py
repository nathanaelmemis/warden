class ClassA:
    def _methodA(self):
        return "MEOW"
    
    def methodB(self):
        print(self._methodA())

class ClassB(ClassA):
    def _methodA(self):
        return "MING"

classA = ClassA()
classB = ClassB()

classA.methodB()
classB.methodB()