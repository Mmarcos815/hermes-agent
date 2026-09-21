'use strict';
// Native + Java SSL bypass for Android 14 (SDK 34-36) — no root needed via frida-server

function hookNative() {
    // Hook SSL_CTX_set_verify to disable verification
    try {
        const SSL_CTX_set_verify = Module.findExportByName(null, 'SSL_CTX_set_verify');
        if (SSL_CTX_set_verify) {
            Interceptor.attach(SSL_CTX_set_verify, {
                onEnter: function(args) {
                    console.log('[NATIVE] SSL_CTX_set_verify called, setting mode to 0 (SSL_VERIFY_NONE)');
                    args[1] = ptr(0); // SSL_VERIFY_NONE
                }
            });
            console.log('[NATIVE] SSL_CTX_set_verify hooked');
        }
    } catch (e) { console.log('[NATIVE] no SSL_CTX_set_verify: ' + e.message); }

    // Hook X509_verify_cert to always return 1 (success)
    try {
        const X509_verify_cert = Module.findExportByName(null, 'X509_verify_cert');
        if (X509_verify_cert) {
            Interceptor.replace(X509_verify_cert, new NativeCallback(function(ctx) {
                console.log('[NATIVE] X509_verify_cert bypassed, returning 1');
                return 1;
            }, 'int', ['pointer']));
            console.log('[NATIVE] X509_verify_cert hooked');
        }
    } catch (e) { console.log('[NATIVE] no X509_verify_cert: ' + e.message); }

    // Hook SSL_get_verify_result to always return X509_V_OK (0)
    try {
        const SSL_get_verify_result = Module.findExportByName(null, 'SSL_get_verify_result');
        if (SSL_get_verify_result) {
            Interceptor.replace(SSL_get_verify_result, new NativeCallback(function(ssl) {
                return 0; // X509_V_OK
            }, 'long', ['pointer']));
            console.log('[NATIVE] SSL_get_verify_result hooked');
        }
    } catch (e) { console.log('[NATIVE] no SSL_get_verify_result: ' + e.message); }

    // Hook SSL_do_handshake to return 1 (success)
    try {
        const SSL_do_handshake = Module.findExportByName(null, 'SSL_do_handshake');
        if (SSL_do_handshake) {
            Interceptor.attach(SSL_do_handshake, {
                onLeave: function(retval) {
                    console.log('[NATIVE] SSL_do_handshake result: ' + retval);
                }
            });
            console.log('[NATIVE] SSL_do_handshake hooked');
        }
    } catch (e) { console.log('[NATIVE] no SSL_do_handshake: ' + e.message); }

    console.log('[NATIVE] ALL NATIVE HOOKS INSTALLED');
}

function hookJava() {
    Java.perform(() => {
        // Conscrypt TrustManagerImpl
        try {
            const TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
            TrustManagerImpl.verifyChain.implementation = (untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) => {
                console.log('[JAVA] verifyChain bypassed for: ' + host);
                return untrustedChain;
            };
            console.log('[JAVA] TrustManagerImpl.verifyChain hooked');
        } catch (e) { console.log('[JAVA] no TrustManagerImpl: ' + e.message); }

        // OkHttp CertificatePinner
        try {
            const CertificatePinner = Java.use('okhttp3.CertificatePinner');
            CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = (host, certs) => {
                console.log('[JAVA] OkHttp check bypassed for: ' + host);
            };
            console.log('[JAVA] OkHttp CertificatePinner hooked');
        } catch (e) { console.log('[JAVA] no OkHttp pinner: ' + e.message); }

        // X509TrustManager
        try {
            const X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
            X509TrustManager.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = (chain, authType) => {
                console.log('[JAVA] X509TM checkServerTrusted bypassed');
            };
            console.log('[JAVA] X509TrustManager hooked');
        } catch (e) { console.log('[JAVA] no X509TM: ' + e.message); }

        // CLEARTEXT
        try {
            const NetworkSecurityPolicy = Java.use('android.security.net.config.NetworkSecurityPolicy');
            NetworkSecurityPolicy.isCleartextTrafficPermitted.overload().implementation = () => true;
            NetworkSecurityPolicy.isCleartextTrafficPermitted.overload('java.lang.String').implementation = (host) => true;
            console.log('[JAVA] NetworkSecurityPolicy CLEARTEXT allowed');
        } catch (e) { console.log('[JAVA] no NSP: ' + e.message); }

        console.log('[JAVA] ALL JAVA HOOKS INSTALLED');
    });
}

hookNative();
hookJava();
