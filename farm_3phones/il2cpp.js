// il2cpp UnityWebRequest URL + body logger (read-only, own session)
send("[il2cpp ready]");
var _m = Process.findModuleByName("libil2cpp.so"); send("[il2cpp] mod: " + _m); var base = _m.base;
if (!base) { send("[il2cpp] libil2cpp.so NOT loaded"); }
else {
    function istr(p) {
        try {
            if (p.isNull()) return "";
            var len = p.add(0x10).readS32();
            if (len <= 0 || len > 8192) return "";
            return p.add(0x14).readUtf16String(len) || "";
        } catch (e) { return ""; }
    }
    var getUrl = new NativeFunction(base.add(0x2b5a86c), "pointer", ["pointer"]);
    var sendAddr = base.add(0x2b5a174);
    Interceptor.attach(sendAddr, {
        onEnter: function (args) {
            try { send("[url] " + istr(getUrl(args[0])).slice(0, 300)); } catch (e) {}
        }
    });
    send("[il2cpp] SendWebRequest hooked");
    var getText = new NativeFunction(base.add(0x2b58d3c), "pointer", ["pointer"]);
    Interceptor.attach(base.add(0x2b59144), {
        onEnter: function (args) { this.dh = args[0]; },
        onLeave: function () {
            try {
                var t = istr(getText(this.dh)).slice(0, 500);
                if (/mintpull|token|balance|pack|checkin|reward|Bearer|success/i.test(t)) send("[body] " + t);
            } catch (e) {}
        }
    });
    send("[il2cpp] ReceiveData hooked");
}
send("[il2cpp armed]");
