import base64, json
with open('farm_3phones/now_phone03.png', 'rb') as f:
    data = f.read()
    with open('/dev/stdout', 'wb') as out:
        out.write(data)
