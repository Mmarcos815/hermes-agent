import zipfile
import re

d = zipfile.ZipFile("apks/outpost.apk").read("assets/index.android.bundle").decode("utf-8", "ignore")
for pat, label in [(r"\.from\('([A-Za-z_]+)'\)", "FROM1"), (r'\.from\("([A-Za-z_]+)"\)', "FROM2"),
                   (r"\.rpc\('([A-Za-z_]+)'", "RPC1"), (r'\.rpc\("([A-Za-z_]+)"', "RPC2")]:
    print(label, sorted(set(re.findall(pat, d)))[:20])
