// frida_tcgp.js - DNS + TCP logging for Pokémon TCG Live
send("[frida] script loaded");

function exp(mod, name) {
    try { return Module.getExportByName(mod, name); } catch(e) {}
    try { return Module.findExportByName(mod, name); } catch(e) {}
    return null;
}

// Hook getaddrinfo for DNS
var getaddrinfo = exp("libc.so", "getaddrinfo");
if (getaddrinfo) {
    Interceptor.attach(getaddrinfo, {
        onEnter: function(args) {
            try {
                var hostname = Memory.readUtf8String(args[0]);
                if (hostname && hostname.length > 3) {
                    send("[DNS] " + hostname);
                }
            } catch(e) {}
        }
    });
    send("[frida] getaddrinfo hooked");
}

// Hook connect for TCP
var connect = exp("libc.so", "connect");
if (connect) {
    Interceptor.attach(connect, {
        onEnter: function(args) {
            try {
                var sa = args[1];
                var family = Memory.readU16(sa);
                if (family === 2) {
                    var port = ((Memory.readU8(sa.add(2)) << 8) | Memory.readU8(sa.add(3)));
                    var ip = Memory.readU8(sa.add(4)) + "." +
                             Memory.readU8(sa.add(5)) + "." +
                             Memory.readU8(sa.add(6)) + "." +
                             Memory.readU8(sa.add(7));
                    send("[TCP] " + ip + ":" + port);
                }
            } catch(e) {}
        }
    });
    send("[frida] connect hooked");
}

// Find the app's network service threads by monitoring /proc/self/net/tcp
send("[frida] ready - watching for DNS lookups and TCP connections");
