class A:
    stuff = []

    def __init__(self):
        self.stuff.append(1)
class B(A):
    def __init__(self):
        self.stuff.append(2)

a = A()
print(a.stuff)
b = B()
print(a.stuff)
print(b.stuff)
