import os, bs4, datetime, smtplib, threading, requests, __future__
import urllib.request
import pandas as pd
from lxml import html

#żeby wysłać załącznik html
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import email

#wyłączenie pojawiania się błędu pd "SettingWithCopyWarning"
pd.options.mode.chained_assignment = None

url = 'http://notowania.pb.pl/stocktable/GPWAKCJE'
request = urllib.request.Request(url)
response = urllib.request.urlopen(request)
soup = bs4.BeautifulSoup(response, 'lxml')

indeks = 0
spolka = " "
lista_spolek = []


for a in soup.find_all('a', href=True):
   b = str(a['href'])
   if b.startswith('/instrument/'):  
        indeks = indeks + 1
        spolka = b[12:24]
        lista_spolek = lista_spolek + [spolka]
      
newdata = pd.DataFrame({"SPÓŁKA":lista_spolek,"CENA":[0]*indeks,"OFERTA KUPNA":[0]*indeks,"OFERTA SPRZEDAŻY":[0]*indeks,"WOLUMEN":[0]*indeks,"C/Z":[0]*indeks,"LINK":[0]*indeks})
   
r = 0
indeks = 0

def feeling_data(wiersz, ISIN):
   url = 'https://www.gpw.pl/spolka?isin=' + ISIN
   url_ind = 'https://notowania.pb.pl/instrument/' + ISIN
   
   try:    
      strona = requests.get(url)
      tree = html.fromstring(strona.text)
      strona_ind = requests.get(url_ind)
      tree_ind = html.fromstring(strona_ind.text)
      xpath_cena = tree.xpath('/html/body/section[2]/div/div[2]/div[2]/div/span')[0].text
      xpath_oferta_k = tree.xpath('/html/body/section[3]/div[2]/div/div[1]/table[1]/tbody/tr[1]/td[2]')[0].text
      xpath_oferta_s = tree.xpath('/html/body/section[3]/div[2]/div/div[1]/table[1]/tbody/tr[2]/td[2]')[0].text
      xpath_wolumen = tree.xpath('/html/body/section[3]/div[2]/div/div[1]/table[1]/tbody/tr[3]/td[2]')[0].text
      try:
         xpath_c_z = tree_ind.xpath('/html/body/div[3]/div[2]/div[6]/div[3]/div[2]/div[2]/div[4]/div[4]/div[2]/table/tbody/tr[6]/td[2]')[0].text
      except:
         xpath_c_z = 0

         
      slownik_xpath = {"CENA":xpath_cena,
                        "OFERTA KUPNA":xpath_oferta_k,
                        "OFERTA SPRZEDAŻY":xpath_oferta_s,
                        "WOLUMEN":xpath_wolumen,
                        "C/Z":xpath_c_z,
                        "LINK":url}

      
      for kolumna, wartosc in slownik_xpath.items():
         try:
            wartosc = wartosc.replace(",", ".")
            wartosc = int(wartosc)
               
         except:
            ()
         newdata[kolumna][wiersz] = wartosc
            
   except:         
      pusty_slownik = {"CENA":0,
                       "OFERTA KUPNA":0,
                       "OFERTA SPRZEDAŻY":0,
                       "WOLUMEN":0,
                       "C/Z":0,
                       "LINK":url}

      for kolumna, wartosc in pusty_slownik.items():
         newdata[kolumna][wiersz] = wartosc


ii = "" 
q = 0

while True:
   downloadThreads = []
   for j in range(0,100):
      try:
         downloadThread = threading.Thread(target=feeling_data, args=(q, lista_spolek[q]))
         downloadThreads.append(downloadThread)
         downloadThread.start()
         q = q + 1
         #ii = "koniec"
      except:
         ii = "koniec"
         break
   for downloadThread in downloadThreads:
      downloadThread.join()
   if ii == "koniec":
      break


newdata["CENA"] = pd.to_numeric(newdata["CENA"], errors='coerce').fillna(0)
newdata["OFERTA KUPNA"] = pd.to_numeric(newdata["OFERTA KUPNA"], errors='coerce').fillna(0)
newdata["OFERTA SPRZEDAŻY"] = pd.to_numeric(newdata["OFERTA SPRZEDAŻY"], errors='coerce').fillna(0)
newdata["WOLUMEN"] = pd.to_numeric(newdata["WOLUMEN"], errors='coerce').fillna(0)
newdata["C/Z"] = pd.to_numeric(newdata["C/Z"], errors='coerce').fillna(0)

newdata["OPŁACALNOŚĆ"] = newdata["OFERTA KUPNA"] / newdata["CENA"]
newdata["OPŁACALNOŚĆ"] = pd.to_numeric(newdata["OPŁACALNOŚĆ"], errors='coerce').fillna(0) #usuwam błędy powodowane przez wartości NaN
newdata.sort_values(by = "OPŁACALNOŚĆ", ascending=False)

os.chdir("D:\\PROGRAMOWANIE\\PYTHON\\AUTOMAT FOREX\\STEM GPW")


#
#
#filtrowanie danych
newdata = newdata[(newdata['WOLUMEN'] > 50.00)
                  & (newdata['C/Z'] < 7.00 )
                  & (newdata['C/Z'] > 0)
                  & (newdata["OPŁACALNOŚĆ"] < 0.98)
                  & (newdata["OPŁACALNOŚĆ"] > 0)]


#
#
#wysyłanie wiadomości email z załącznikiem

od = 'radek.87@onet.eu'
do = 'kozlowski.radoslaw.pl@gmail.com'

msg = MIMEMultipart()
msg['Subject'] = "STEM przesyła wiadomość"
msg['From'] = od
msg['To'] = do

konw = newdata.to_html("D:\\PROGRAMOWANIE\\PYTHON\\AUTOMAT FOREX\\STEM GPW\\NOWY.html")
filename = "D:\\PROGRAMOWANIE\\PYTHON\\AUTOMAT FOREX\\STEM GPW\\NOWY.html"

part = MIMEBase('application', "octet-stream")
part.set_payload(open(filename, "rb").read())
email.encoders.encode_base64(part)
part.add_header('Content-Disposition', 'attachment; filename="analiza.html"')
msg.attach(part)

smtpObj = smtplib.SMTP('smtp.poczta.onet.pl', 587)
smtpObj.ehlo()
smtpObj.starttls()
smtpObj.login('radek.87@onet.eu', 'rkleonid1')
smtpObj.sendmail(od, do, msg.as_string()) 
smtpObj.quit()

