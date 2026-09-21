// hunt_endpoints.js - Frida script: hook lib il2cpp and log HTTP(S) calls
'use strict';

// 1) Log outgoing connections from any socket syscall
const sockets = Module.getExportByName(null, 'connect');
if (sockets) {
  Interceptor.attach(sockets, {
    onEnter: function(args) {
      this.host = args[1].readUtf8String();
      send(`[SOCKET] connect to ${this.host}`);
    }
  });
}

// 2) Hook libcurl if present (many Unity games use it)
const curl = Module.getExportByName('libcurl.so', 'curl_easy_perform');
if (curl) {
  Interceptor.attach(curl, {
    onEnter: function(args) {
      const handle = args[0];
      // curl_easy_getinfo(handle, CURLINFO_URL, &url) — can't call easily,
      // just note the handle exists
      send(`[CURL] easy_perform handle=${handle}`);
    }
  });
}

// 3) Hook Java Network (Unity on Android may use Java URL connection too)
Java.perform(function() {
  try {
    const HttpURLConnection = Java.use('java.net.HttpURLConnection');
    HttpURLConnection.setRequestMethod.implementation = function(method) {
      send(`[JAVA HTTP] ${method} ${this.getURL()}`);
      return this.setRequestMethod(method);
    };
  } catch(e) {
    // not loaded yet
  }
});

// 4) Unity WWW / UnityWebRequest
// These live in il2cpp symbols if present — we'll scan in il2cpp hook
send('[HUNT] script ready');
