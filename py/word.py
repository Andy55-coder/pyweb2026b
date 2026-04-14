def square(y):
	print(f"{y}的三次方是{y**3}")




x = int(input("請輸入一個整數:"))
#x += 10

if(x<=0):
	print(f"您輸入的值是{x},小於等於0")
else:
    print(f"您輸入的值是{x},大於0")
    for i in range(1, x+1):
     	#print(i, end=";")
     	square(i)
