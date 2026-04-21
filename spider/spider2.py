import requests
from bs4 import BeautifulSoup

url = "https://pyweb2026b-haz9.vercel.app/about"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("#pic")

for item in result:
	print(item)
	print(item.get("src"))
	print()

