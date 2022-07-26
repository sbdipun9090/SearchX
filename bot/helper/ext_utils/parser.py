import base64
import re
import requests
import cloudscraper

from lxml import etree
from urllib.parse import urlparse, parse_qs

from bot import UNIFIED_EMAIL, UNIFIED_PASS, GDTOT_CRYPT, HUBDRIVE_CRYPT, KATDRIVE_CRYPT, DRIVEFIRE_CRYPT, XSRF_TOKEN, laravel_session
from bot.helper.ext_utils.exceptions import ExceptionHandler

account = {
    'email': UNIFIED_EMAIL,
    'passwd': UNIFIED_PASS
}

def account_login(client, url, email, password):
    data = {
        'email': email,
        'password': password
    }
    client.post(f'https://{urlparse(url).netloc}/login', data=data)

def gen_payload(data, boundary=f'{"-"*6}_'):
    data_string = ''
    for item in data:
        data_string += f'{boundary}\r\n'
        data_string += f'Content-Disposition: form-data; name="{item}"\r\n\r\n{data[item]}\r\n'
    data_string += f'{boundary}--\r\n'
    return data_string

def appdrive(url: str) -> str:
    if (UNIFIED_EMAIL or UNIFIED_PASS) is None:
        raise ExceptionHandler("UNIFIED_EMAIL and UNIFIED_PASS env vars not provided")
    client = requests.Session()
    client.headers.update({
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
    })
    account_login(client, url, account['email'], account['passwd'])
    res = client.get(url)
    try:
        key = re.findall(r'"key",\s+"(.*?)"', res.text)[0]
    except IndexError:
        raise ExceptionHandler("Invalid link")
    ddl_btn = etree.HTML(res.content).xpath("//button[@id='drc']")
    info = {}
    info['error'] = False
    info['link_type'] = 'login'  # direct/login
    headers = {
        "Content-Type": f"multipart/form-data; boundary={'-'*4}_",
    }
    data = {
        'type': 1,
        'key': key,
        'action': 'original'
    }
    if len(ddl_btn):
        info['link_type'] = 'direct'
        data['action'] = 'direct'
    while data['type'] <= 3:
        try:
            response = client.post(url, data=gen_payload(data), headers=headers).json()
            break
        except:
            data['type'] += 1
    if 'url' in response:
        info['gdrive_link'] = response['url']
    elif 'error' in response and response['error']:
        info['error'] = True
        info['message'] = response['message']
    if urlparse(url).netloc == 'driveapp.in' and not info['error']:
        res = client.get(info['gdrive_link'])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn')]/@href")[0]
        info['gdrive_link'] = drive_link
    if urlparse(url).netloc == 'drivesharer.in' and not info['error']:
        res = client.get(info['gdrive_link'])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn btn-primary')]/@href")[0]
        info['gdrive_link'] = drive_link
    if urlparse(url).netloc == 'drivebit.in' and not info['error']:
        res = client.get(info['gdrive_link'])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn btn-primary')]/@href")[0]
        info['gdrive_link'] = drive_link
    if urlparse(url).netloc == 'driveace.in' and not info['error']:
        res = client.get(info['gdrive_link'])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn btn-primary')]/@href")[0]
        info['gdrive_link'] = drive_link
    if urlparse(url).netloc == 'drivelinks.in' and not info['error']:
        res = client.get(info['gdrive_link'])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn btn-primary')]/@href")[0]
        info['gdrive_link'] = drive_link
    if urlparse(url).netloc == 'drivepro.in' and not info['error']:
        res = client.get(info['gdrive_link'])
        drive_link = etree.HTML(res.content).xpath("//a[contains(@class,'btn btn-primary')]/@href")[0]
        info['gdrive_link'] = drive_link
    if not info['error']:
        return info['gdrive_link']
    else:
        raise ExceptionHandler(f"{info['message']}")

def gdtot(url: str) -> str:
    if GDTOT_CRYPT is None:
        raise ExceptionHandler("GDTOT_CRYPT env var not provided")
    client = requests.Session()
    client.cookies.update({'crypt': GDTOT_CRYPT})
    res = client.get(url)
    res = client.get(f"https://new.gdtot.nl/dld?id={url.split('/')[-1]}")
    url = re.findall(r'URL=(.*?)"', res.text)[0]
    info = {}
    info['error'] = False
    params = parse_qs(urlparse(url).query)
    if 'gd' not in params or not params['gd'] or params['gd'][0] == 'false':
        info['error'] = True
        if 'msgx' in params:
            info['message'] = params['msgx'][0]
        else:
            info['message'] = 'Invalid link'
    else:
        decoded_id = base64.b64decode(str(params['gd'][0])).decode('utf-8')
        drive_link = f'https://drive.google.com/open?id={decoded_id}'
        info['gdrive_link'] = drive_link
    if not info['error']:
        return info['gdrive_link']
    else:
        raise ExceptionHandler(f"{info['message']}")
        
def parse_info(res, url):
    info_parsed = {}
    if 'drivebuzz' in url:
        info_chunks = re.findall('<td\salign="right">(.*?)<\/td>', res.text)
    else:
        info_chunks = re.findall('>(.*?)<\/td>', res.text)
    for i in range(0, len(info_chunks), 2):
        info_parsed[info_chunks[i]] = info_chunks[i+1]
    return info_parsed

def udrive(url: str) -> str:
    client = cloudscraper.create_scraper(delay=10, browser='chrome')
    if 'hubdrive' in url:
        client.cookies.update({'crypt': HUBDRIVE_CRYPT})
    if 'drivehub' in url:
        client.cookies.update({'crypt': KATDRIVE_CRYPT})
    if 'katdrive' in url:
        client.cookies.update({'crypt': KATDRIVE_CRYPT})
    if 'kolop' in url:
        client.cookies.update({'crypt': KATDRIVE_CRYPT})
    if 'drivefire' in url:
        client.cookies.update({'crypt': DRIVEFIRE_CRYPT})
    if 'drivebuzz' in url:
        client.cookies.update({'crypt': DRIVEFIRE_CRYPT})
        
    res = client.get(url)
    info_parsed = parse_info(res, url)
    info_parsed['error'] = False
    
    up = urlparse(url)
    req_url = f"{up.scheme}://{up.netloc}/ajax.php?ajax=download"
    
    file_id = url.split('/')[-1]
    
    data = { 'id': file_id }
    
    headers = {
        'x-requested-with': 'XMLHttpRequest'
    }
    
    try:
        res = client.post(req_url, headers=headers, data=data).json()['file']
    except: return {'error': True, 'src_url': url}
    
    if 'drivefire' in url:
        decoded_id = res.rsplit('/', 1)[-1]
        flink = f"https://drive.google.com/file/d/{decoded_id}"
        return flink
    elif 'drivehub' in url:
        gd_id = res.rsplit("=", 1)[-1]
        flink = f"https://drive.google.com/open?id={gd_id}"
        return flink
    elif 'drivebuzz' in url:
        gd_id = res.rsplit("=", 1)[-1]
        flink = f"https://drive.google.com/open?id={gd_id}"
        return flink
    else:
        gd_id = re.findall('gd=(.*)', res, re.DOTALL)[0]
 
    info_parsed['gdrive_url'] = f"https://drive.google.com/open?id={gd_id}"
    info_parsed['src_url'] = url
    flink = info_parsed['gdrive_url']

    return flink

def parse_infos(res):
    f = re.findall(">(.*?)<\/td>", res.text)
    info_parsed = {}
    for i in range(0, len(f), 3):
        info_parsed[f[i].lower().replace(' ', '_')] = f[i+2]
    return info_parsed

def sharer_pw(url, forced_login=False):
    client = cloudscraper.create_scraper(delay=10, browser='chrome')
    
    client.cookies.update({
        "XSRF-TOKEN": XSRF_TOKEN,
        "laravel_session": laravel_session
    })
    
    res = client.get(url)
    token = re.findall("token\s=\s'(.*?)'", res.text, re.DOTALL)[0]
    
    ddl_btn = etree.HTML(res.content).xpath("//button[@id='btndirect']")
    
    info_parsed = parse_infos(res)
    info_parsed['error'] = True
    info_parsed['src_url'] = url
    info_parsed['link_type'] = 'login' # direct/login
    info_parsed['forced_login'] = forced_login
    
    headers = {
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    data = {
        '_token': token
    }
    
    if len(ddl_btn):
        info_parsed['link_type'] = 'direct'
    if not forced_login:
        data['nl'] = 1
    
    try: 
        res = client.post(url+'/dl', headers=headers, data=data).json()
    except:
        return info_parsed
    
    if 'url' in res and res['url']:
        info_parsed['error'] = False
        info_parsed['gdrive_link'] = res['url']
        
    if len(ddl_btn) and not forced_login and not 'url' in info_parsed:
        # retry download via login
        return sharer_pw(url, forced_login=True)
    
    flink = info_parsed['gdrive_link']
    return flink
