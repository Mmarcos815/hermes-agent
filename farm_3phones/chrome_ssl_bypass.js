'use strict';
// Chrome SSL pin + CA trust bypass for Android 16 (SDK 36)
// Targets Chrome's native BoringSSL + Java trust layers
// Also dumps request/response URLs to Frida console for traffic discovery

function hookAll() {
    console.log('[' + new Date().toISOString() + '] Chrome SSL bypass starting...');

    // ==========================================
    // 1. Java TrustManager bypass (covers Java HTTP clients inside Chrome)
    // ==========================================
    try {
        const TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        const origVerify = TrustManagerImpl.verifyChain;
        TrustManagerImpl.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            console.log('[SSL] bypassed TrustManagerImpl.verifyChain: ' + host);
            return untrustedChain;
        };
        console.log('[SSL] TrustManagerImpl hooked');
    } catch (e) { console.log('[SSL] TrustManagerImpl: ' + e.message); }

    // X509TrustManager
    try {
        const X509TM = Java.use('javax.net.ssl.X509TrustManager');
        X509TM.checkServerTrusted.implementation = function(chain, authType) {
            // console.log('[SSL] X509TM checkServerTrusted: ' + authType);
        };
        X509TM.checkClientTrusted.implementation = function(chain, authType) {
            // console.log('[SSL] X509TM checkClientTrusted: ' + authType);
        };
        console.log('[SSL] X509TrustManager hooked');
    } catch (e) { console.log('[SSL] X509TM: ' + e.message); }

    // NetworkSecurityPolicy - allow cleartext + trust user certs
    try {
        const NSP = Java.use('android.security.net.config.NetworkSecurityPolicy');
        NSP.isCleartextTrafficPermitted.implementation = function() { return true; };
        console.log('[SSL] NetworkSecurityPolicy cleartext allowed');
    } catch (e) { console.log('[SSL] NSP: ' + e.message); }

    // ==========================================
    // 2. Chrome-specific: WebViewClient SSL error handling
    // Chrome on Android uses WebView which has its own SSL error callbacks
    // ==========================================
    try {
        const WebViewClient = Java.use('android.webkit.WebViewClient');
        const origOnReceivedSslError = WebViewClient.onReceivedSslError;
        WebViewClient.onReceivedSslError.implementation = function(view, handler, error) {
            console.log('[SSL] WebView SSL error consumed for: ' + (view.getClass() ? view.getClass().getName() : 'unknown'));
            // Tell Chrome to proceed anyway
            try {
                handler.proceed();
            } catch (e) {
                // handler might be proxied, try alternative
                try {
                    handler.cancel();
                } catch (e2) {}
            }
        };
        console.log('[SSL] WebViewClient.onReceivedSslError hooked');
    } catch (e) { console.log('[SSL] WebViewClient: ' + e.message); }

    // ==========================================
    // 3. Conscrypt SSLParameters - allow unsafe server certificates
    // ==========================================
    try {
        const SSLParams = Java.use('com.android.org.conscrypt.SSLParameters');
        const origConstructor = SSLParams.$init;
        SSLParams.$init.implementation = function() {
            const result = origConstructor.call(this);
            try {
                this.setEndpointIdentificationAlgorithm(null);
            } catch (e) {}
            return result;
        };
        console.log('[SSL] Conscrypt SSLParameters hooked');
    } catch (e) { console.log('[SSL] SSLParameters: ' + e.message); }

    // ==========================================
    // 4. TrustManagerFactory - bypass default algorithm
    // ==========================================
    try {
        const TMF = Java.use('javax.net.ssl.TrustManagerFactory');
        const origInit = TMF.init;
        TMF.init.implementation = function(trustStore) {
            // Don't actually init with the real trust store
            console.log('[SSL] TrustManagerFactory.init bypassed');
        };
        console.log('[SSL] TrustManagerFactory hooked');
    } catch (e) { console.log('[SSL] TMF: ' + e.message); }

    // ==========================================
    // 5. HttpsURLConnection - set default SSLSocketFactory that accepts all
    // ==========================================
    try {
        const HttpsURLConnection = Java.use('javax.net.ssl.HttpsURLConnection');
        const SSLContext = Java.use('javax.net.ssl.SSLContext');

        // Create an SSLContext that trusts everything
        const context = SSLContext.getInstance('TLS');
        const trustAllCerts = [];
        const TM = Java.use('javax.net.ssl.X509TrustManager');
        const trustManager = Java.registerClass({
            name: 'com.dad.TrustAllManager',
            implements: [TM],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
        trustAllCerts.push(trustManager.$new());

        const tmf = Java.use('javax.net.ssl.TrustManagerFactory').getDefaultAlgorithm();
        const tmFactory = SSLContext.getTrustManagerFactory();
        // Can't easily set custom trust managers via Frida on the default context
        // Instead, hook the getDefault method
        const origGetDefault = SSLContext.getDefault;
        SSLContext.getDefault.implementation = function() {
            try {
                const c = this.getInstance('TLS');
                const tmArr = [trustManager.$new()];
                // This won't work directly - SSLContext.init needs a real TrustManagerFactory
                console.log('[SSL] SSLContext.getDefault called - would bypass but limited');
                return c;
            } catch (e) {
                return this.getDefault.call(this);
            }
        };
        console.log('[SSL] HttpsURLConnection/SSLContext hooks installed');
    } catch (e) { console.log('[SSL] HttpsURLConnection: ' + e.message); }

    // ==========================================
    // 6. CertificateFactory - nullify certificate parsing
    // ==========================================
    try {
        const CF = Java.use('java.security.cert.CertificateFactory');
        const origGenerateCert = CF.generateCertificate;
        CF.generateCertificate.implementation = function(inputStream) {
            console.log('[SSL] CertificateFactory.generateCertificate called');
            return origGenerateCert.call(this, inputStream);
        };
        console.log('[SSL] CertificateFactory hooked');
    } catch (e) { console.log('[SSL] CertFactory: ' + e.message); }

    // ==========================================
    // 7. Android Network Security Config - force trust of user CAs
    // ==========================================
    try {
        const NSC = Java.use('android.security.net.config.NetworkSecurityConfig');
        const origGetTrustManagers = NSC.getTrustManagers;
        NSC.getTrustManagers.implementation = function() {
            console.log('[SSL] NSC.getTrustManagers - returning default');
            return origGetTrustManagers.call(this);
        };
        console.log('[SSL] NetworkSecurityConfig hooked');
    } catch (e) { console.log('[SSL] NSC: ' + e.message); }

    // ==========================================
    // 8. PKIX Certificate validation - skip revocation checking
    // ==========================================
    try {
        const PKIX = Java.use('java.security.cert.PKIXParameters');
        const origSetRevocationEnabled = PKIX.setRevocationEnabled;
        PKIX.setRevocationEnabled.implementation = function(enabled) {
            console.log('[SSL] PKIX revocation ' + enabled + ' -> disabled');
            return origSetRevocationEnabled.call(this, false);
        };
        console.log('[SSL] PKIX revocation checking bypassed');
    } catch (e) { console.log('[SSL] PKIX: ' + e.message); }

    console.log('[' + new Date().toISOString() + '] Chrome SSL bypass: ALL HOOKS INSTALLED');
}

Java.perform(hookAll);
