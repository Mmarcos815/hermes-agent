import zipfile
import re

SKIP = (b"google", b"facebook", b"apple", b"unity", b"w3.org", b"sentry",
        b"opentelemetry", b"android.com", b"app-measurement", b"onesignal",
        b"sumsub", b"appsflyer", b"example", b"cloudflare", b"crbug",
        b"goo.gl", b"goo.gle", b"fb.gg", b"opentelemetry")

z = zipfile.ZipFile("apks/mintpull.apk")
dex = b"".join(z.read(n) for n in z.namelist() if n.endswith(".dex"))
urls = sorted(set(re.findall(rb"https://[a-z0-9.\-]+\.[a-z]{2,}", dex)))
for u in urls:
    if not any(s in u for s in SKIP):
        print(u.decode())
