import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)


import requests
from bs4 import BeautifulSoup
url = "http://www.atmovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"

sp = BeautifulSoup(Data.text, "html.parser")
updateDate = sp.find("div", class_="smaller09").text
result=sp.select(".filmListAllX li")
lastUpdate = sp.find("div", class_="smaller09").text[5:]

info = ""
for item in result:
  picture = item.find("img").get("src").replace(" ", "")
  title = item.find("div", class_="filmtitle").text
  movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")

  hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")

  show = item.find("div", class_="runtime").text.replace("上映日期：", "")
  showDate = show[0:10]
  if "片長" in show:
    show = show.replace("片長：", "")
    show = show.replace("分", "")
    showLength = show[13:].replace(" ", "")

  else:
    showLength = "尚無片長資訊"

  info += movie_id + "\n" + picture + "\n" + title + "\n" + hyperlink + "\n" + showDate + "\n" + showLength + "\n\n"

  doc = {
      "title": title,
      "picture": picture,
      "hyperlink": hyperlink,
      "showDate": showDate,
      "showLength": showLength,
      "lastUpdate": lastUpdate
  }

  db = firestore.client()
  doc_ref = db.collection("電影2A").document(movie_id)
  doc_ref.set(doc)

info += updateDate + "\n\n"

print(info)
