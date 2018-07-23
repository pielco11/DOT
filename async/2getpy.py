import re
import asyncio
import aiohttp
from aiohttp_socks import SocksConnector, SocksVer
from datetime import datetime
import json
import hashlib
import urllib.parse
import time

import sys
sys.setrecursionlimit(100000)

from bs4 import BeautifulSoup
from tqdm import tqdm

import validate_bitcoin
import validate_email

fullLink = {}
__tot_links = []

class RateLimiter:
  """Rate limits an HTTP client that would make get() and post() calls.
  Calls are rate-limited by host.
  https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
  This class is not thread-safe."""
  RATE = 2000
  MAX_TOKENS = 2000

  def __init__(self, client):
    self.client = client
    self.tokens = self.MAX_TOKENS
    self.updated_at = time.monotonic()

  async def get(self, *args, **kwargs):
    await self.wait_for_token()
    return self.client.get(*args, **kwargs)

  async def wait_for_token(self):
    while self.tokens < 1:
      self.add_new_tokens()
      await asyncio.sleep(0.1)
    self.tokens -= 1

  def add_new_tokens(self):
    now = time.monotonic()
    time_since_update = now - self.updated_at
    new_tokens = time_since_update * self.RATE
    if new_tokens > 1:
      self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
      self.updated_at = now



def filterEmails(email):
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
  _emails = re.findall('[a-zA-Z0-9\.\-+_]+@[a-zA-Z0-9\.\-+_]+\.[a-zA-Z0-9]+', soup.get_text())
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
  __tot_links.append(urllib.parse.urljoin(domain, link))
  print("<==> {} \n {} \n {} \n len: {}".format(domain, urllib.parse.urljoin(domain, link), datetime.now(), len(__tot_links)))
  await fetch(urllib.parse.urljoin(domain, link))

async def fetch(domain):
  domain = "{}".format(domain.strip("\n"))
  try:
    if domain.split('/')[2] in lists:
      if not (domain.endswith("gz") or domain.endswith("tar") or domain.endswith("rpm") or domain.endswith("jpg")
        or domain.endswith("bz2") or domain.endswith("drpm") or domain.endswith("zip") or domain.endswith("filez")
        or domain.endswith("dirtree")):
        conn = SocksConnector(
               socks_ver=SocksVer.SOCKS5,
               host='127.0.0.1',
               port=9050,
               rdns=True)
        ua = {'User-Agent': 'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/0.8.12'}
        async with aiohttp.ClientSession(connector=conn, headers=ua) as session:
          session = RateLimiter(session)
          async with await session.get(domain) as response:
            if response.status == 200:
              soup = BeautifulSoup(await response.read(), "html.parser")
              for link in soup.find_all('a'):
                _t_url = urllib.parse.urljoin(domain, link.get('href'))
                if not _t_url in fullLink[domain.split('/')[2]]:
                  fullLink[domain.split('/')[2]].append(_t_url)
                  await getContent(domain, soup, link.get('href'))
            else:
              _obj = {
                "status": response.status,
                "domain": domain,
                "@timestamp": str(datetime.now())
                }
              outList.write(json.dumps(_obj) + ",")
  except IndexError:
    pass


#domList = open("/home/user/BitBucket/DarkNetOSINT/deepCrawl/all_http.txt", "r").readlines()
domList = open("200.txt").readlines()
outList = open("report-14-07-18_6_s.json", "a")
outList.write("[")

tasks = []
lists = []
loop = asyncio.get_event_loop()
for i in range(5):
  lists.append(domList[i+5].strip('\n').split('/')[2])
  task = asyncio.ensure_future(fetch(domList[i+5]))
  fullLink.update({domList[i+5].strip('\n').split('/')[2]: []})
  tasks.append(task)
#task = asyncio.ensure_future(run(['pastebin.com/kvPAAkxQ']))
#tasks.append(task)
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
outList.write("]")
outList.close()
