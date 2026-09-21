import base64, json, sys
with open(sys.argv[1], 'rb') as f:
    data = f.read()
    b64 = base64.b64encode(data).decode()
    print(json.dumps({"data": b64}))
