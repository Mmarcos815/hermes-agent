// netlog: print every DNS + TCP connect from this app (read-only)
function exp(mod, name) {
    try { return Module.getExportByName(mod, name); } catch (e) {}
    try { return Module.findExportByName(mod, name); } catch (e) {}
    return null;
}
var getaddrinfo = exp("libc.so", "getaddrinfo");
if (getaddrinfo) {
    Interceptor.attach(getaddrinfo, {
        onEnter: function (args) {
            try { send("[dns] " + Memory.readUtf8String(args[0])); } catch (e) {}
        }
    });
}
var connect = exp("libc.so", "connect");
if (connect) {
    Interceptor.attach(connect, {
        onEnter: function (args) {
            try {
                var sa = args[1];
                var family = Memory.readU16(sa);
                if (family === 2) {
                    var port = ((Memory.readU8(sa.add(2)) << 8) | Memory.readU8(sa.add(3)));
                    var ip = Memory.readU8(sa.add(4)) + "." + Memory.readU8(sa.add(5)) + "." + Memory.readU8(sa.add(6)) + "." + Memory.readU8(sa.add(7));
                    send("[tcp] " + ip + ":" + port);
                }
            } catch (e) {}
        }
    });
}
send("[netlog ready]");
