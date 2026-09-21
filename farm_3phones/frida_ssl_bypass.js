'use strict';
// Rip Rush (com.emeraldmyth.riprush.and) — SSL Pinning Bypass v2
// Phone-02: 192.168.1.158:35493  |  mitmproxy :8081/:8082
//
// Fixes over v1:
//   (a) OkHttp Builder.certificatePinner returns `this` (was recursive)
//   (b) Conscrypt TrustManagerImpl uses correct 6-param verifyChain sig
//   (c) Native SSL hooks: SSL_CTX_set_verify, X509_verify_cert, SSL_get_verify_result
//   (d) UnityWebRequest.SetCertificateHandler for Unity Java binding
//
// Run: frida -U -f com.emeraldmyth.riprush.and -l farm_3phones/frida_ssl_bypass.js --no-pause

console.log('[BYPASS] === Rip Rush SSL Pinning Bypass v2 loaded ===');

function hookJava() {
  Java.perform(() => {

    // 1. OkHttp3.CertificatePinner.check - drop pin validation
    try {
      const Pinner = Java.use('okhttp3.CertificatePinner');
      Pinner.check.overload('java.lang.String', 'java.util.List')
        .implementation = function(host, pins) {
          console.log('[PIN] OkHttp CertificatePinner.check(' + host + ')  BYPASSED');
        };
      console.log('[PIN] OkHttp3.CertificatePinner.check hooked');
    } catch (e) {
      console.log('[PIN] OkHttp3.CertificatePinner not found: ' + e.message);
    }

    // 2. OkHttpClient.Builder.certificatePinner - FIXED: return this, not recursive
    try {
      const Builder = Java.use('okhttp3.OkHttpClient$Builder');
      Builder.certificatePinner.implementation = function(pinner) {
        console.log('[PIN] OkHttpClient.Builder.certificatePinner(pinner)  strip, return builder');
        if (pinner !== null && pinner !== undefined) {
          console.log('[PIN]   (original pinner ignored)');
        }
        return this;
      };
      console.log('[PIN] OkHttpClient.Builder.certificatePinner hooked');
    } catch (e) {
      console.log('[PIN] OkHttpClient$Builder not found: ' + e.message);
    }

    // 3. X509TrustManager.checkServerTrusted - blanket trust-all
    try {
      const TM = Java.use('javax.net.ssl.X509TrustManager');
      TM.checkServerTrusted.overload(
        '[Ljava.security.cert.X509Certificate;', 'java.lang.String'
      ).implementation = function(chain, authType) {
        console.log('[PIN] X509TrustManager.checkServerTrusted  BYPASSED');
      };
      console.log('[PIN] X509TrustManager.checkServerTrusted hooked');
    } catch (e) {
      console.log('[PIN] X509TrustManager not found: ' + e.message);
    }

    // 4. Conscrypt TrustManagerImpl.verifyChain - correct 6-param sig for SDK 34-36
    try {
      const CTM = Java.use('com.android.org.conscrypt.TrustManagerImpl');
      CTM.verifyChain.implementation = function(
        untrustedChain, trustAnchorChain, host,
        clientAuth, ocspData, tlsSctData
      ) {
        console.log('[PIN] Conscrypt TrustManagerImpl.verifyChain(' + host + ')  BYPASSED (return chain)');
        return untrustedChain;
      };
      console.log('[PIN] Conscrypt TrustManagerImpl.verifyChain hooked');
    } catch (e) {
      console.log('[PIN] Conscrypt TrustManagerImpl not found: ' + e.message);
    }

    // 5. HostnameVerifier.verify - accept any hostname
    try {
      const HV = Java.use('javax.net.ssl.HostnameVerifier');
      HV.verify.implementation = function(hostname, session) {
        console.log('[PIN] HostnameVerifier.verify(' + hostname + ')  true');
        return true;
      };
      console.log('[PIN] HostnameVerifier hooked');
    } catch (e) {
      console.log('[PIN] HostnameVerifier not found: ' + e.message);
    }

    // 6. WebViewClient.onReceivedSslError - proceed on SSL error
    try {
      const WV = Java.use('android.webkit.WebViewClient');
      WV.onReceivedSslError.implementation = function(view, handler, error) {
        console.log('[PIN] WebViewClient.onReceivedSslError  handler.proceed()');
        handler.proceed();
      };
      console.log('[PIN] WebViewClient.onReceivedSslError hooked');
    } catch (e) {
      console.log('[PIN] WebViewClient not found: ' + e.message);
    }

    // 7. HttpsURLConnection - neutralise default SSL config
    try {
      const Https = Java.use('javax.net.ssl.HttpsURLConnection');
      Https.setDefaultSSLSocketFactory.implementation = function(factory) {
        console.log('[PIN] HttpsURLConnection.setDefaultSSLSocketFactory  ignored');
      };
      Https.setDefaultHostnameVerifier.implementation = function(v) {
        console.log('[PIN] HttpsURLConnection.setDefaultHostnameVerifier  ignored');
      };
      console.log('[PIN] HttpsURLConnection defaults hooked');
    } catch (e) {
      console.log('[PIN] HttpsURLConnection not found: ' + e.message);
    }

    // 8. OkHttp3.Call.execute - log outgoing requests
    try {
      const Call = Java.use('okhttp3.Call');
      Call.execute.implementation = function() {
        try {
          const req = this.request();
          const url = req.url().toString();
          console.log('[REQ] ' + req.method() + ' ' + url);
        } catch (e) {}
        return this.execute();
      };
      console.log('[PIN] OkHttp3.Call.execute hooked (request logging)');
    } catch (e) {
      console.log('[PIN] OkHttp3.Call not found for logging: ' + e.message);
    }

    // 9. UnityWebRequest.SetCertificateHandler - Unity Java binding
    try {
      const UW = Java.use('UnityEngine.Networking.UnityWebRequest');
      UW.SetCertificateHandler.implementation = function(handler) {
        console.log('[PIN] UnityWebRequest.SetCertificateHandler  no-op (trust-all)');
      };
      console.log('[PIN] UnityWebRequest.SetCertificateHandler hooked');
    } catch (e) {
      console.log('[PIN] UnityWebRequest Java binding not found (likely pure IL2CPP): ' + e.message);
    }

    console.log('[PIN] === all Java hooks installed ===');
  });
}

function hookNative() {
  console.log('[NATIVE] attempting native SSL hooks...');

  // SSL_CTX_set_verify(ctx, mode, cb)  set mode=SSL_VERIFY_NONE (0)
  try {
    const f = Module.findExportByName(null, 'SSL_CTX_set_verify');
    if (f) {
      Interceptor.attach(f, {
        onEnter: function(args) {
          console.log('[NATIVE] SSL_CTX_set_verify(ctx=0x' + args[0].toString().substr(0,18) + ', mode=' + args[1].toInt32() + ')');
          args[1] = ptr(0);
        }
      });
      console.log('[NATIVE] SSL_CTX_set_verify hooked  SSL_VERIFY_NONE');
    } else {
      console.log('[NATIVE] SSL_CTX_set_verify not exported');
    }
  } catch (e) { console.log('[NATIVE] SSL_CTX_set_verify hook failed: ' + e.message); }

  // X509_verify_cert(ctx)  always return 1
  try {
    const f = Module.findExportByName(null, 'X509_verify_cert');
    if (f) {
      Interceptor.replace(f, new NativeCallback(function(ctx) { return 1; }, 'int', ['pointer']));
      console.log('[NATIVE] X509_verify_cert hooked  always 1');
    } else {
      console.log('[NATIVE] X509_verify_cert not exported');
    }
  } catch (e) { console.log('[NATIVE] X509_verify_cert hook failed: ' + e.message); }

  // SSL_get_verify_result(ssl)  always return 0
  try {
    const f = Module.findExportByName(null, 'SSL_get_verify_result');
    if (f) {
      Interceptor.replace(f, new NativeCallback(function(ssl) { return 0; }, 'int', ['pointer']));
      console.log('[NATIVE] SSL_get_verify_result hooked  always 0');
    } else {
      console.log('[NATIVE] SSL_get_verify_result not exported');
    }
  } catch (e) { console.log('[NATIVE] SSL_get_verify_result hook failed: ' + e.message); }

  // SSL_do_handshake  log only
  try {
    const f = Module.findExportByName(null, 'SSL_do_handshake');
    if (f) {
      Interceptor.attach(f, {
        onLeave: function(retval) { console.log('[NATIVE] SSL_do_handshake  ' + retval.toString()); }
      });
      console.log('[NATIVE] SSL_do_handshake hooked (logging only)');
    } else {
      console.log('[NATIVE] SSL_do_handshake not exported');
    }
  } catch (e) { console.log('[NATIVE] SSL_do_handshake hook failed: ' + e.message); }

  console.log('[NATIVE] === native hook pass complete ===');
}

hookNative();
hookJava();

console.log('[BYPASS] === Rip Rush SSL Pinning Bypass v2 ACTIVE ===');
console.log('[BYPASS] Check mitmweb.log for 192.168.1.158  zero failed lines = clean.');
