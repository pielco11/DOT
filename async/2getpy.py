import re
import asyncio
import aiohttp
from aiosocksy.connector import ProxyConnector, ProxyClientRequest
from datetime import datetime
import json
import hashlib
import urllib.parse

from bs4 import BeautifulSoup
from tqdm import tqdm

import validate_bitcoin
import validate_email

fullLink = []

def filterEmails(email):
  if validate_email.validate_email(email):
    try:
      if validate_email.validate_email(email, check_mx=False):
        return "",email
      else:
        return email,""
    except:
      return email,""

def filterBitcoin(bitcoin):
  try:
    if validate_bitcoin.validate(bitcoin):
      return bitcoin
    else:
      return ""
  except:
    return ""

async def getContent(domain, soup, link):
  if soup.title:
    title = soup.title.string
  else:
    title = "no-title"
  _emails = re.findall('[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+', soup.get_text())
  _onionServices = re.findall('[a-zA-Z0-9]{16}.onion', soup.get_text())
  _btcAddresses = re.findall('[13][a-km-zA-HJ-NP-Z1-9]{25,34}', soup.get_text())
  for _e in _emails:
    _f_ems, _v_ems = filterEmails(_e)
    _d_obj = {
      "domain": domain,
      "@timestamp": str(datetime.now()),
      "status": 200,
      "title": title,
      "link": urllib.parse.urljoin(domain, link),
      "valid_emails": _v_ems,
      "fake_emails": _f_ems
    }
    outList.write(json.dumps(_d_obj) + ",")
  for _b in _btcAddresses:
    _btc = filterBitcoin(_b)
    if _btc:
      _d_obj = {
        "domain": domain,
        "@timestamp": str(datetime.now()),
        "status": 200,
        "title": title,
        "link": urllib.parse.urljoin(domain, link),
        "bitcoin": _btc
      }
      outList.write(json.dumps(_d_obj) + ",")
  for _hs in _onionServices:
    _d_obj = {
      "domain": domain,
      "@timestamp": str(datetime.now()),
      "status": 200,
      "title": title,
      "link": urllib.parse.urljoin(domain, link),
      "onion_service": _hs
    }
    outList.write(json.dumps(_d_obj) + ",")
  #outList.write(json.dumps(fullz))
  print("<==> {} \n {} \n {}".format(domain, urllib.parse.urljoin(domain, link), datetime.now()))
  await fetch(urllib.parse.urljoin(domain, link))

async def getLinks(domain, soup):
  links = soup.find_all('a')
  for link in links:
    if not urllib.parse.urljoin(domain, link.get('href')) in fullLink:
      fullLink.append(urllib.parse.urljoin(domain, link.get('href')))
      await getContent(domain, soup, link.get('href'))

async def fetch(domain):
  try:
    if domain.split('/')[2] in str(lists):
      if not (domain.endswith("gz") or domain.endswith("tar") or domain.endswith("rpm") or domain.endswith("jpg")
          or domain.endswith("bz2") or domain.endswith("drpm") or domain.endswith("zip") or domain.endswith("filez")
          or domain.endswith("dirtree")):
        conn = ProxyConnector(remote_resolve=True)
        ua = {'User-Agent': 'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/0.8.12'}
        async with aiohttp.ClientSession(connector=conn, request_class=ProxyClientRequest, headers=ua) as session:
          async with session.get(domain, proxy='socks5://127.0.0.1:9050') as response:
            if response.status == 200:
              soup = BeautifulSoup(await response.read(), "html5lib")
              await getLinks(domain, soup)
            else:
              _obj = {
                "status": response.status, 
                "domain": domain, 
                "@timestamp": str(datetime.now())
                }
              outList.write(json.dumps(_obj) + ",")
  except Exception as e:
    print(" !!! Error: {} \n{}".format(domain, e))
    pass


#domList = open("/home/user/BitBucket/DarkNetOSINT/deepCrawl/all_http.txt", "r").readlines()
domList = open("200.txt").readlines()
outList = open("report-14-07-18.json", "a")
outList.write("[")

#bar = tqdm(domList)
async def run(dom):
  #bar = tqdm(domList)
  #bar.update()
  #for doms in list:
  _domain = "{}".format(dom.strip("\n"))
  await fetch(_domain)
    
tasks = []
lists = []
loop = asyncio.get_event_loop()
for i in range(20):
  lists.append(domList[i])
  task = asyncio.ensure_future(run(domList[i]))
  tasks.append(task)
#task = asyncio.ensure_future(run(['pastebin.com/kvPAAkxQ']))
#tasks.append(task)
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
outList.write("]")
outList.close()
