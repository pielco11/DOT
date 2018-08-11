import re
import asyncio
from datetime import datetime
import urllib.parse
import time
import sqlite3
import sys
import contextlib
import hashlib
from bs4 import BeautifulSoup
import aiohttp
from aiohttp_socks import SocksConnector, SocksVer
from elasticsearch import Elasticsearch, helpers
from cashaddress import convert
import validate_email

class RecycleObject(object):
    """Object to clean the stdout
    """
    def write(self, junk): pass
    def flush(self): pass

@contextlib.contextmanager
def nostdout():
    """Method to clean the stdout
    """
    savestdout = sys.stdout
    sys.stdout = RecycleObject()
    yield
    sys.stdout = savestdout

sys.setrecursionlimit(100000)

__tot_links = 0
es = Elasticsearch(["localhost:9200"])

def init_db(db):
    """Connect to the db return cursor
    """
    try:
        _conn = sqlite3.connect(db)
        cursor = _conn.cursor()
        table_urls = """
            CREATE TABLE IF NOT EXISTS
                urls (
                    domain text not null,
                    url text,
                    PRIMARY KEY (domain, url)
                );
        """
        cursor.execute(table_urls)
        table_emails = """
            CREATE TABLE IF NOT EXISTS
                emails (
                    domain text not null,
                    timestamp text not null,
                    status integer,
                    title text,
                    link text,
                    valid_emails text,
                    fake_emails text,
                    partial text
                );
        """
        cursor.execute(table_emails)
        table_bitcoins = """
            CREATE TABLE IF NOT EXISTS
                bitcoins (
                    domain text not null,
                    timestamp text not null,
                    status integer,
                    title text,
                    link text,
                    bitcoin text,
                    partial text
                )
        """
        cursor.execute(table_bitcoins)
        table_hses = """
            CREATE TABLE IF NOT EXISTS
                hses (
                    domain text not null,
                    timestamp text not null,
                    status integer,
                    title text,
                    link text,
                    onion_service text,
                    partial_text text
                )
        """
        cursor.execute(table_hses)
        return _conn
    except Exception as e:
        print(e)
        sys.exit(1)

def add_D_db(domain, url):
    """Add the url of the given domain into the db
    """
    try:
        cursor = conn.cursor()
        entry = (domain, url,)
        query = "INSERT INTO urls VALUES (?,?)"
        cursor.execute(query, entry)
        conn.commit()
    except sqlite3.IntegrityError:
        print(" [x] IntegrityError")

def add_E_db(domain, timestamp, status, title, link, valid_emails, fake_emails, partial):
    """Add emails of the given webpage into the db
    """
    try:
        cursor = conn.cursor()
        entry = (domain, timestamp, status, title, link, valid_emails, fake_emails, partial,)
        query = "INSERT INTO emails VALUES (?,?,?,?,?,?,?,?)"
        cursor.execute(query, entry)
        conn.commit()
    except sqlite3.IntegrityError:
        print(" [x] IntegrityError")

def add_B_db(domain, timestamp, status, title, link, bitcoin, partial):
    """Add bitcoin addresses of the given webpage into the db
    """
    try:
        cursor = conn.cursor()
        entry = (domain, timestamp, status, title, link, bitcoin, partial,)
        query = "INSERT INTO bitcoins VALUES (?,?,?,?,?,?,?)"
        cursor.execute(query, entry)
        conn.commit()
    except sqlite3.IntegrityError:
        print(" [x] IntegrityError")

def add_H_db(domain, timestamp, status, title, link, hs, partial):
    """Add bitcoin addresses of the given webpage into the db
    """
    try:
        cursor = conn.cursor()
        entry = (domain, timestamp, status, title, link, hs, partial,)
        query = "INSERT INTO hses VALUES (?,?,?,?,?,?,?)"
        cursor.execute(query, entry)
        conn.commit()
    except sqlite3.IntegrityError:
        print(" [x] IntegrityError")

def getD_db(domain):
    """Returns urls from db given a domain
    """
    cursor = conn.execute("SELECT url FROM urls WHERE domain = ?", (domain, ))
    return cursor

def getU_db(url):
    """Returns urls from db given a domain
    """
    cursor = conn.execute("SELECT url FROM urls WHERE url = ?", (url, ))
    return cursor

class RateLimiter:
    """Rate limits an HTTP client that would make get() and post() calls.
    Calls are rate-limited by host.
    https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
    This class is not thread-safe."""
    RATE = 2500
    MAX_TOKENS = 2500

    def __init__(self, client):
        self.client = client
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        """The new method GET
        """
        await self.wait_for_token()
        return self.client.get(*args, **kwargs)

    async def wait_for_token(self):
        """Wait for token released
        """
        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.1)
        self.tokens -= 1

    def add_new_tokens(self):
        """Add new tokens
        """
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.RATE
        if new_tokens > 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now

def filterEmails(email):
    """Filter email address
    """
    try:
        if validate_email.validate_email(email, check_mx=False):
            return "", email
        return email, ""
    except:
        return email, ""

def filterBitcoin(bitcoin):
    """Filter bitcoin address
    """
    if convert.is_valid(bitcoin):
        return bitcoin
    return ""

async def getContent(domain, soup, link):
    """Get content from webpage
    """
    _jData = []
    global __tot_links
    if soup.title:
        title = soup.title.string
    else:
        title = "no-title"
    _emails = re.findall('[a-zA-Z0-9\.\-+_]+@[a-zA-Z0-9\.\-+_]+\.[a-zA-Z0-9]+', soup.get_text())
    _onionServices = re.findall('[a-zA-Z0-9]{16}.onion', soup.get_text())
    _btcAddresses = re.findall('[13][a-km-zA-HJ-NP-Z1-9]{25,34}', soup.get_text())
    for _e in _emails:
        _f_ems, _v_ems = filterEmails(_e)
        _partial_text = soup.get_text().split(_e)
        _id = domain + urllib.parse.urljoin(domain, link) + _v_ems + _f_ems
        _now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _link = urllib.parse.urljoin(domain, link)
        _partial = _partial_text[0][-250:0] + _partial_text[1][:250]
        if not _f_ems:
            _d_obj = {
                "_index": "darkasync",
                "_type": "items",
                "_id": hashlib.sha256(_id.encode("utf-8")).hexdigest(),
                "_source": {
                    "domain": domain,
                    "timestamp": _now,
                    "status": 200,
                    "title": title,
                    "link": _link,
                    "valid_emails": _v_ems,
                    "partial_text": _partial
                    }
                }
        else:
            _d_obj = {
                "_index": "darkasync",
                "_type": "items",
                "_id": hashlib.sha256(_id.encode("utf-8")).hexdigest(),
                "_source": {
                    "domain": domain,
                    "timestamp": _now,
                    "status": 200,
                    "title": title,
                    "link": _link,
                    "fake_emails": _f_ems,
                    "partial_text": _partial
                    }
                }
        add_E_db(domain, _now, 200, title, link, _v_ems, _f_ems, _partial)
        _jData.append(_d_obj)
    for _b in _btcAddresses:
        _btc = filterBitcoin(_b)
        _id = domain + urllib.parse.urljoin(domain, link) + _btc
        _partial_text = soup.get_text().split(_b)
        _now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _link = urllib.parse.urljoin(domain, link)
        _partial = _partial_text[0][-250:0] + _partial_text[1][:250]
        if _btc:
            _d_obj = {
                "_index": "darkasync",
                "_type": "items",
                "_id": hashlib.sha256(_id.encode("utf-8")).hexdigest(),
                "_source": {
                    "domain": domain,
                    "timestamp": _now,
                    "status": 200,
                    "title": title,
                    "link": _link,
                    "bitcoin": _btc,
                    "partial_text": _partial
                    }
                }
            add_B_db(domain, _now, 200, title, link, _btc, _partial)
            #print(" [*] btc: {}".format(_btc))
            _jData.append(_d_obj)
    for _hs in _onionServices:
        _id = domain + urllib.parse.urljoin(domain, link) + _hs
        _partial_text = soup.get_text().split(_hs)
        _now = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        _link = urllib.parse.urljoin(domain, link)
        _partial = _partial_text[0][-250:0] + _partial_text[1][:250]
        _d_obj = {
            "_index": "darkasync",
            "_type": "items",
            "_id": hashlib.sha256(_id.encode("utf-8")).hexdigest(),
            "_source": {
                "domain": domain,
                "timestamp": _now,
                "status": 200,
                "title": title,
                "link": _link,
                "onion_service": _hs,
                "partial_text": _partial
                }
            }
        add_H_db(domain, _now, 200, title, _link, _hs, _partial)
        _jData.append(_d_obj)
    __tot_links = __tot_links + 1
    _utp = urllib.parse.urljoin(domain, link)
    print("<==> {} \n {} \n {} \n len: {}".format(domain, _utp, datetime.now(), __tot_links))
    add_D_db(domain.split("/")[2], _utp)
    print(" Added to db: {} :: {}".format(domain.split("/")[2], _utp))
    #with nostdout():
    #helpers.bulk(es, _jData, chunk_size=2000, request_timeout=200)
    _jData = []
    await fetch(urllib.parse.urljoin(domain, link))

async def fetch(domain):
    """Fetch some data
    """
    rows = getD_db(domain.split("/")[2])
    _t_list = []
    for row in rows:
        _t_list.append(row[0])
    try:
        _t_list.remove("http://" + domain.split("/")[2])
    except ValueError:
        pass # the domain is not in list, cannot be removed
    if domain not in _t_list:
        try:
            if domain.split('/')[2] in lists:
                if not (domain.endswith("gz") or domain.endswith("tar") or
                        domain.endswith("rpm") or domain.endswith("jpg") or
                        domain.endswith("bz2") or domain.endswith("drpm") or
                        domain.endswith("zip") or domain.endswith("filez") or
                        domain.endswith("dirtree")):
                    connector = SocksConnector(
                        socks_ver=SocksVer.SOCKS5,
                        host='127.0.0.1',
                        port=9050,
                        rdns=True)
                    ua = {'User-Agent': 'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/0.8.12'}
                    timeout = aiohttp.ClientTimeout(total=60*3)
                    async with aiohttp.ClientSession(connector=connector, headers=ua) as session:
                        session = RateLimiter(session)
                        try:
                            async with await session.get(domain, timeout=timeout) as response:
                                if response.status == 200:
                                    soup = BeautifulSoup(await response.read(), "html.parser")
                                    for link in soup.find_all('a'):
                                        try:
                                            _l = urllib.parse.urljoin(domain, link.get('href'))
                                            rows = getU_db(_l)
                                            _t_list_url = []
                                            for row in rows:
                                                _t_list_url.append(row[0])
                                            if _l not in _t_list_url:
                                                await getContent(domain, soup, link.get('href'))
                                        except Exception as e:
                                            print(e)
                        except Exception as e:
                            #_obj = {
                            #    "domain": domain,
                            #    "timestamp": str(datetime.now()),
                            #    "error": str(e)
                            #    }
                            pass
        except Exception as e:
            print(e)


#domList = open("/home/user/BitBucket/DarkNetOSINT/deepCrawl/all_http.txt", "r").readlines()
domList = open("200.txt").readlines()

#### init db
conn = init_db("db.sqlite3")

tasks = []
lists = []
loop = asyncio.get_event_loop()
u = 520
for i in range(20):
    _dom = domList[i+u].strip('\n')
    lists.append(_dom.split('/')[2])
    task = asyncio.ensure_future(fetch(_dom))
    tasks.append(task)
#task = asyncio.ensure_future(run(['pastebin.com/kvPAAkxQ']))
#tasks.append(task)
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
