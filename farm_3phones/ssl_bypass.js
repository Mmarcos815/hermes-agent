'use strict';
// Universal SSL pinning bypass — adapted for Android 14 (SDK 34-36)
// Handles: Conscrypt TrustManagerImpl, OkHttp 3/4, X509TrustManager, CLEARTEXT detection

function hookAll() {
    // Conscrypt TrustManagerImpl (Android 7+)
    try {
        const TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.verifyChain.implementation = (untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) => {
            console.log('[PIN] bypassed verifyChain for: ' + host);
            return untrustedChain;
        };
        console.log('[PIN] TrustManagerImpl.verifyChain hooked');
    } catch (e) { console.log('[PIN] no TrustManagerImpl: ' + e.message); }

    // OkHttp CertificatePinner (3.x)
    try {
        const CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = (host, certs) => {
            console.log('[PIN] OkHttp check bypassed for: ' + host);
        };
        console.log('[PIN] OkHttp CertificatePinner.check hooked');
    } catch (e) { console.log('[PIN] no OkHttp3 pinner: ' + e.message); }

    // OkHttp CertificatePinner.check(String, Certificate[])
    try {
        const CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = (host, certs) => {
            console.log('[PIN] OkHttp check(cert[]) bypassed for: ' + host);
        };
    } catch (e) {}

    // X509TrustManager checkServerTrusted
    try {
        const X509TrustManager = Java.use('javax.net.ssl.X509TrustManager');
        X509TrustManager.checkServerTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = (chain, authType) => {
            console.log('[PIN] X509TM checkServerTrusted bypassed');
        };
        X509TrustManager.checkClientTrusted.overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = (chain, authType) => {
            console.log('[PIN] X509TM checkClientTrusted bypassed');
        };
        console.log('[PIN] X509TrustManager hooked');
    } catch (e) { console.log('[PIN] no X509TM: ' + e.message); }

    // CLEARTEXT allow
    try {
        const NetworkSecurityPolicy = Java.use('android.security.net.config.NetworkSecurityPolicy');
        NetworkSecurityPolicy.isCleartextTrafficPermitted.overload().implementation = () => true;
        NetworkSecurityPolicy.isCleartextTrafficPermitted.overload('java.lang.String').implementation = (host) => true;
        console.log('[PIN] NetworkSecurityPolicy CLEARTEXT allowed');
    } catch (e) { console.log('[PIN] no NSP: ' + e.message); }

    console.log('[PIN] ALL HOOKS INSTALLED');
}

Java.perform(hookAll);
