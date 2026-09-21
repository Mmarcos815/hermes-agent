// mbedtls verify kill (Unity native TLS) - read-only bypass on own session
send("[mbed ready]");
function kill(name) {
    var p = null;
    try { p = Module.getExportByName("libil2cpp.so", name); } catch (e) {}
    if (!p) {
        var mods = Process.enumerateModules();
        for (var i = 0; i < mods.length; i++) {
            try { p = Module.getExportByName(mods[i].name, name); if (p) break; } catch (e) {}
        }
    }
    if (p) {
        Interceptor.replace(p, new NativeCallback(function () { return 0; }, "int", ["pointer", "pointer", "pointer", "pointer", "pointer", "pointer"]));
        send("[mbed] killed " + name);
    }
    return !!p;
}
var ok = kill("mbedtls_x509_crt_verify_with_profile") || kill("mbedtls_x509_crt_verify");
if (!ok) send("[mbed] symbols not found");
send("[mbed armed]");
