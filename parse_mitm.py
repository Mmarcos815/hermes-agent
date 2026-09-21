import re

with open('farm_3phones/phone01.mitm', 'rb') as f:
    data = f.read().decode('utf-8', errors='ignore')

flows = data.split('}2:id;')
print(f'Approximate flows: {len(flows)}')

hosts = set()
for fl in flows:
    for m in re.finditer(r'4:path;[^;]*?,9:authority;0:,6:scheme;[^:]*?,[^:]*?:([^;]+);', fl):
        hosts.add(m.group(1))
    for m in re.finditer(r'4:port;[^:]*?#4:host;([^;]+);', fl):
        hosts.add(m.group(1))

addrs = set()
for m in re.finditer(r'server connect ([^:]+):\d+ \(([0-9.]+)', data):
    addrs.add(f'{m.group(1)} ({m.group(2)})')

print(f'\nUnique target hosts: {len(hosts)}')
for h in sorted(hosts):
    if h and len(h) > 3:
        print(h)

print(f'\nUpstream connections: {len(addrs)}')
for a in sorted(addrs):
    print(a)
