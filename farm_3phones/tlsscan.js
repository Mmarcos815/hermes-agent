// find TLS verify exports across all modules (read-only enum)
send("[scan start]");
var hits = [];
Process.enumerateModules().forEach(function (m) {
    try {
        Module.enumerateExports(m.name).forEach(function (e) {
            var n = e.name.toLowerCase();
            if ((n.indexOf("verify") !== -1 || n.indexOf("x509") !== -1) && n.indexOf("ssl") !== -1) {
                hits.push(m.name + "!" + e.name);
            }
        });
    } catch (err) {}
});
send("[scan] ssl-verify hits: " + JSON.stringify(hits.slice(0, 20)));
var hits2 = [];
Process.enumerateModules().forEach(function (m) {
    try {
        Module.enumerateExports(m.name).forEach(function (e) {
            var n = e.name.toLowerCase();
            if (n.indexOf("mbedtls") !== -1 || n.indexOf("ssl_ctx") !== -1 || n.indexOf("ssl_set") !== -1) {
                hits2.push(m.name + "!" + e.name);
            }
        });
    } catch (err) {}
});
send("[scan] mbed hits: " + JSON.stringify(hits2.slice(0, 20)));
send("[scan done]");
