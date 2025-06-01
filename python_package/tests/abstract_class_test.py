from abc import ABC, abstractmethod


class InterfaceA(ABC):
    def methodA(self):
        print("MEOW")

    @abstractmethod
    def methodB():
        pass

class ClassA(InterfaceA):
    def methodB(self):
        print("MING")

classA = ClassA()

classA.methodA()
classA.methodB()