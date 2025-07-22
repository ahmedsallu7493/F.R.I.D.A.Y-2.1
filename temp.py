from Backend.temp2 import HandGestureController
from Backend.Model import firstlayer

n=input("Enter your choice:")
decision=firstlayer(n)

if (decision == 'control'):
    HandGestureController().run()
else:
    print("Other Decision ")