import re, glob

SKIP = (b"googleapis.com", b"gstatic.com", b"google.com", b"facebook.com", b"apple.com",
        b"unity3d.com", b"w3.org", b"schema.org", b"stripe.com", b"paypal.com")

for f in sorted(glob.glob("farm_3phones/apks/*.apk")):
    print("=" * 20, f)
    data = open(f, "rb").read()
    urls = sorted(set(re.findall(rb"https://[a-z0-9.\-]+(?:\.[a-z]{2,})(?::[0-9]+)?(?:/[A-Za-z0-9._/\-]*)?", data)))
    shown = 0
    for u in urls:
        if any(s in u for s in SKIP):
            continue
        try:
            print(" ", u.decode()[:120])
        except Exception:
            pass
        shown += 1
        if shown >= 45:
            break
