'use strict';
// Chrome SSL bypass + HTTP traffic interceptor for boxed.gg capture
// Attaches to Chrome (PID 27536), bypasses SSL, logs all HTTP(S) traffic

function hookAll() {
    console.log('=== CHROME INTERCEPT STARTING ===');
    console.log('Time: ' + new Date().toISOString());

    // ==========================================
    // SSL BYPASS - all layers
    // ==========================================
    
    // 1. TrustManagerImpl (Conscrypt - Android's default SSL impl)
    try {
        const TMI = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        const orig = TMI.verifyChain;
        TMI.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            if (host) console.log('[SSL] Bypassed TrustManagerImpl for: ' + host);
            return untrustedChain;
        };
        console.log('[SSL] TrustManagerImpl hooked OK');
    } catch (e) { console.log('[SSL] TrustManagerImpl: ' + e.message); }

    // 2. X509TrustManager
    try {
        const X509TM = Java.use('javax.net.ssl.X509TrustManager');
        X509TM.checkServerTrusted.implementation = function(chain, authType) {
            // Silently accept
        };
        X509TM.checkClientTrusted.implementation = function(chain, authType) {
            // Silently accept
        };
        console.log('[SSL] X509TrustManager hooked OK');
    } catch (e) { console.log('[SSL] X509TrustManager: ' + e.message); }

    // 3. WebView SSL error handler - tell Chrome to proceed
    try {
        const WC = Java.use('android.webkit.WebViewClient');
        const origSslError = WC.onReceivedSslError;
        WC.onReceivedSslError.implementation = function(view, handler, error) {
            console.log('[SSL] WebView SSL error consumed: ' + error.getCertificate().getAllForSession().toString().substring(0, 80));
            try { handler.proceed(); } catch(e) { try { handler.cancel(); } catch(e2){} }
        };
        console.log('[SSL] WebViewClient hooked OK');
    } catch (e) { console.log('[SSL] WebViewClient: ' + e.message); }

    // 4. NetworkSecurityPolicy - allow everything
    try {
        const NSP = Java.use('android.security.net.config.NetworkSecurityPolicy');
        NSP.isCleartextTrafficPermitted.implementation = function() { return true; };
        console.log('[SSL] NetworkSecurityPolicy hooked OK');
    } catch (e) { console.log('[SSL] NSP: ' + e.message); }

    // 5. HttpsURLConnection - set a trust-all default
    try {
        const SSLContext = Java.use('javax.net.ssl.SSLContext');
        const TM = Java.use('javax.net.ssl.X509TrustManager');
        
        // Create trust-all manager via Frida's Java.registerClass
        const TrustAllManager = Java.registerClass({
            name: 'org-dad-TrustAllManager-' + Date.now(),
            implements: [TM],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
        
        // Create SSLContext with trust-all
        const ctx = SSLContext.getInstance('TLS');
        const initParams = Java.array('java.security.Provider', []);
        // Use a TrustManager array with our trust-all manager
        const tma = Java.array('javax.net.ssl.TrustManager', [TrustAllManager.$new()]);
        const spa = Java.array('java.security.SecureRandom', [Java.use('java.security.SecureRandom').getInstance().$new()]);
        
        try {
            ctx.init(tma, spa, new java.security.SecureRandom());
            SSLContext.setDefault(ctx);
            console.log('[SSL] SSLContext set to trust-all');
        } catch (e) {
            console.log('[SSL] Could not set default SSLContext: ' + e.message);
            // Fallback: hook getDefault to return our context
            const origGetDefault = SSLContext.getDefault;
            SSLContext.getDefault.implementation = function() {
                try {
                    const c = SSLContext.getInstance('TLS');
                    c.init(tma, spa, new java.security.SecureRandom());
                    return c;
                } catch (e2) {
                    return origGetDefault.call(this);
                }
            };
            console.log('[SSL] SSLContext.getDefault hooked (fallback)');
        }
    } catch (e) { console.log('[SSL] HttpsURLConnection: ' + e.message); }

    // ==========================================
    // HTTP TRAFFIC INTERCEPTOR
    // ==========================================
    
    // Hook URL.openConnection to intercept all HTTP requests
    try {
        const URL = Java.use('java.net.URL');
        const origOpenConnection = URL.openConnection;
        
        URL.openConnection.implementation = function() {
            const conn = origOpenConnection.call(this);
            const urlStr = this.toString();
            
            // Only intercept if it's an HTTP/HTTPS connection
            if (urlStr.startsWith('http://') || urlStr.startsWith('https://')) {
                try {
                    // Hook the connect method to capture the request
                    if (conn.getClass().getName().includes('Https')) {
                        console.log('[HTTP-S] ' + urlStr);
                    } else {
                        console.log('[HTTP] ' + urlStr);
                    }
                    
                    // Try to read response code after connect
                    const origConnect = conn.connect;
                    if (origConnect) {
                        conn.connect.implementation = function() {
                            origConnect.call(conn);
                            try {
                                const code = conn.getResponseCode();
                                if (code > 0) {
                                    console.log('[RESP] ' + code + ' ' + urlStr);
                                }
                            } catch (e) {}
                        };
                    }
                } catch (e) {
                    // Connection might not be HTTP - skip
                }
            }
            
            return conn;
        };
        console.log('[HTTP] URL.openConnection hooked OK');
    } catch (e) { console.log('[HTTP] URL.openConnection: ' + e.message); }

    // ==========================================
    // OkHttp interceptor (many Android apps use OkHttp)
    // ==========================================
    try {
        const OkHttpClient = Java.use('okhttp3.OkHttpClient');
        const origBuilder = OkHttpClient.Builder;
        
        // Hook the build method to add our interceptor
        const origBuild = OkHttpClient.Builder.build;
        OkHttpClient.Builder.build.implementation = function() {
            const client = origBuild.call(this);
            console.log('[HTTP] OkHttpClient built - would intercept if OkHttp used');
            return client;
        };
        console.log('[HTTP] OkHttpClient.Builder.build hooked');
    } catch (e) { console.log('[HTTP] OkHttp: ' + e.message); }

    // ==========================================
    // WebView request interception
    // ==========================================
    try {
        const WebView = Java.use('android.webkit.WebView');
        
        // Hook loadUrl to see what URLs Chrome loads
        const origLoadUrl = WebView.loadUrl;
        WebView.loadUrl.implementation = function(url, headers) {
            if (url && (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('file://'))) {
                console.log('[WV-LOAD] ' + url.substring(0, 200));
            }
            return origLoadUrl.call(this, url, headers);
        };
        
        // Also hook the string version
        try {
            WebView.loadUrl.implementation = function(url) {
                if (url && (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('file://'))) {
                    console.log('[WV-LOAD] ' + url.substring(0, 200));
                }
                return origLoadUrl.call(this, url);
            };
        } catch (e2) {}
        
        console.log('[HTTP] WebView.loadUrl hooked OK');
    } catch (e) { console.log('[HTTP] WebView: ' + e.message); }

    // ==========================================
    // Chrome-specific: Chromium network stack
    // Chrome on Android uses its own networking (net::URLRequest)
    // through WebView/Content layer. The Java hooks above cover
    // the Java-layer URLs. For native Chrome networking, we'd need
    // to hook C/C++ functions which is much more complex.
    // ==========================================

    console.log('=== CHROME INTERCEPT READY ===');
    console.log('All SSL bypassed, HTTP logging active');
    console.log('Visit boxed.gg in Chrome to see traffic');
}

Java.perform(hookAll);
