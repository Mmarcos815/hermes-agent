'use strict';
// Pure Frida HTTP interceptor — no proxy needed
// Hooks OkHttp3 + HttpURLConnection + UnityWebRequest (native)

const hosts = {};

function logHttp() {
    Java.perform(() => {
        // Hook OkHttp3 ResponseBody.string() to capture responses
        try {
            const ResponseBody = Java.use('okhttp3.ResponseBody');
            const Buffer = Java.use('okio.Buffer');
            
            ResponseBody.string.implementation = function() {
                const resp = this;
                const request = resp.request();
                const url = request.url().toString();
                const method = request.method();
                const code = resp.code();
                const body = this.string ? this.string() : 'null';
                
                if (url.includes('cardoutpost') || url.includes('supabase') || url.includes('api.')) {
                    console.log(`[HTTP] ${method} ${url} -> ${code}`);
                    if (body && body.length > 0 && body.length < 10000) {
                        console.log(`[BODY] ${body.substring(0, 5000)}`);
                    }
                }
                return body;
            };
            console.log('[INTERCEPT] ResponseBody.string hooked');
        } catch (e) { console.log('[INTERCEPT] no ResponseBody: ' + e.message); }

        // Hook OkHttp3 interceptors to capture requests
        try {
            const OkHttpClient = Java.use('okhttp3.OkHttpClient');
            const Builder = Java.use('okhttp3.OkHttpClient$Builder');
            Builder.addInterceptor.implementation = (interceptor) => {
                console.log('[INTERCEPT] Interceptor added: ' + interceptor.$className);
                return this.addInterceptor(interceptor);
            };
            console.log('[INTERCEPT] OkHttpClient.Builder hooked');
        } catch (e) { console.log('[INTERCEPT] no OkHttp Builder: ' + e.message); }

        // Hook HttpURLConnection
        try {
            const HttpURLConnection = Java.use('java.net.HttpURLConnection');
            const URL = Java.use('java.net.URL');
            URL.openConnection.overload().implementation = function() {
                const url = this.toString();
                if (url.includes('cardoutpost') || url.includes('supabase') || url.includes('api.')) {
                    console.log('[HTTP] HttpURLConnection.openConnection: ' + url);
                };
                return this.openConnection();
            };
            console.log('[INTERCEPT] HttpURLConnection hooked');
        } catch (e) { console.log('[INTERCEPT] no HttpURLConnection: ' + e.message); }

        // Hook AndroidHttpClient 
        try {
            const AndroidHttpClient = Java.use('android.net.http.AndroidHttpClient');
            AndroidHttpClient.execute.overload('org.apache.http.client.methods.HttpUriRequest').implementation = (req) => {
                console.log('[HTTP] AndroidHttpClient.execute: ' + req.getURI().toString());
                return this.execute(req);
            };
        } catch (e) {}

        // Try to hook React Native fetch (Expo uses OkHttp under the hood, so OkHttp hooks should cover it)
        try {
            const RNHttpClient = Java.use('com.facebook.react.modules.network.NetworkingModule');
            console.log('[INTERCEPT] React Native NetworkingModule found');
        } catch (e) {}

        console.log('[INTERCEPT] JAVA HOOKS INSTALLED');
    });
}

// Native hooks for UnityWebRequest
function hookUnity() {
    try {
        const unity = Process.findModuleByName('libunity.so');
        if (!unity) { console.log('[UNITY] libunity.so not found'); return; }
        
        // Try to find UnityWebRequest functions
        const sendRequest = unity.findExportByName('UnityWebRequest_SendWebRequest');
        if (sendRequest) {
            console.log('[UNITY] Found UnityWebRequest_SendWebRequest at ' + sendRequest);
        }
        
        console.log('[UNITY] libunity.so loaded at ' + unity.base + ' size=' + unity.size);
    } catch (e) { console.log('[UNITY] error: ' + e.message); }
}

logHttp();
hookUnity();
