// unpin: Java TrustManager + BoringSSL native verify (own session)
send("[unpin ready]");
Java.perform(function () {
    ["javax.net.ssl.X509TrustManager", "com.android.org.conscrypt.TrustManagerImpl"].forEach(function (cn) {
        try {
            var M = Java.use(cn);
            M.checkServerTrusted.overloads.forEach(function (ov) {
                ov.implementation = function () { return; };
            });
            send("[unpin] java hooked " + cn);
        } catch (e) { send("[unpin] java skip " + cn); }
    });
});
var libs = ["libssl.so", "libcrypto.so", "libmainlinecronet.141.0.7340.3.so", "libcronet.so"];
var syms = ["X509_verify_cert", "SSL_set_custom_verify", "SSL_CTX_set_verify", "ssl_crypto_x509_verify"];
var done = [];
libs.forEach(function (lib) {
    syms.forEach(function (s) {
        var p = null;
        try { p = Module.getExportByName(lib, s); } catch (e) {}
        if (p && done.indexOf(s) === -1) {
            done.push(s);
            try {
                if (s === "X509_verify_cert") {
                    Interceptor.replace(p, new NativeCallback(function () { return 0; }, "int", ["pointer"]));
                } else if (s === "SSL_set_custom_verify") {
                    Interceptor.attach(p, {
                        onEnter: function (args) { try { args[2].writePointer(ptr(0)); } catch (e) {} }
                    });
                }
                send("[unpin] native hooked " + lib + "!" + s);
            } catch (e) { send("[unpin] native fail " + s + ": " + e); }
        }
    });
});
if (!done.length) send("[unpin] no native symbols");
send("[unpin armed]");
