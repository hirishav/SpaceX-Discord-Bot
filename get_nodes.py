import urllib.request, json
try:
    req = urllib.request.Request('https://raw.githubusercontent.com/DarrenOfficial/lavalink-list/master/docs/NoSSL/lavalink-without-ssl.json', headers={'User-Agent': 'Mozilla/5.0'})
    data = json.loads(urllib.request.urlopen(req).read().decode())
    for n in data:
        if n.get('v4'):
            print(f"http://{n['host']}:{n['port']} ({n['password']})")
except Exception as e:
    print(e)
