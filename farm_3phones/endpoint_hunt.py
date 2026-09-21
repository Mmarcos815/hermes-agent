#!/usr/bin/env python3
"""Endpoint hunter — scan APKs for real URLs, filter framework noise."""
import re, os

SKIP_HOSTS = {
    'googleapis','gstatic','google','facebook','apple','unity3d','w3.org',
    'schema.org','stripe','paypal','playgames','firebase','app-measurement',
    'crbug','goo.gl','goo.gle','fb.gg','opentelemetry','android.com',
    'myrightbird','youtrack','zdassets','gravatar','ns.adobe','schemas.android',
    'schemas.openid','xml.org','xmlpull','chilliant','xap','example.com',
    'blogspot','googlesyndication','appsflyersdk','googleadservices',
    'developers.facebook','developers.google','developer.android',
    'developer.apple','developer.mozilla','expo','swmansion',
    'eascdn','sentry','posthog','vercel','shadertoy','dicebear',
    'myapp','psacard','dhl','fedex','usps','afterpay','checkout.link',
    'support.link','commerce','merchant-ui-api','errors.stripe','hooks.stripe',
    'ay.stripe','pm.stripe','mg.stripecdn','static.afterpay',
    'react-native-google-signin','accounts.google','appleid.apple',
    'stripecdn','cdn.stripe','status.stripe','support.stripe',
    'ingest.sentry','console.aws.amazon','browser.sentry-cdn',
    'blob.vercel-storage','vercel-insights','ingest.sentry',
    'ocs.expo','ocs.stripe','ocs.sentry','ocs.swmansion','ocs.adobe',
    's.adobe','chemas.android','chemas.microsoft','evelop.sentry',
    'lassic-assets','ussets.myapp','ussets.tcgdex','itag','itics.vercel',
    's.i.posthog','u.i.posthog','s-assets.i.posthog','u-assets.i.posthog',
    'g.co','aomedia','dashif','purl.org','filesystem.local','default.url',
    'dev.to','auspost','supabase','cognito','zhegan','mqcdn','spoqa',
    'ifsg','images','static','fonts','ajax','js','css','img','i.','m.','l.',
    'nsp','soap','xap','xlink','sType','DynamicMedia','ResourceEvent',
    'ResourceRef','mm','Dimensions','sType','tps','tpsr','tpsl',
    'decidedat','resendlink','signup','keyrotateinuprighttps',
    'some-stream-name','taKeyRotateInUpRighttps',
    'hortcut','icon','interpretation','language','style','text','years',
    'wencodeuricomponent','botsetintent','frameLightspeedoutright',
    'webparsecodehostnamediumseagreen','enablelayoutanimations',
    'standaloneappstarttracing','etcapturedscopesonspanimate',
    'draweractions','strokeDasharrayStartsWithasHooks',
    'ACCELEROMETER','GestureHandlerButtoneMappingNode',
    'getInternalHeighttps','issueTracker','blob','master','LICENSENTRY',
    'BROWSER_NAME','CHINESE','ENTRY_BROWSER_VERSION','ative',
    'androidx','media','issues','charpeni','react-native-url-polyfill',
    'setInternetCredentialsForServerifyText','effectiveWeighttps',
    'gson','ssembly','Troubleshooting','mrdoob','three.js',
    'database-spans','clipboard','navigationInChildEnabled',
    'LucideClipboardClock','progress-bar-android','M12.5',
    'iosClientId','binaryEncodeUserBroadcastPushNotificationManager',
    'removeNodeFromMapplePayEnabled','LucideCornerLeftDownIconotBefore',
    'adUsageCount','react-native-screens','issuecomment','software-mansion',
    'react-native-reanimated','issue','readmeasure','SourceRect',
    'updateWeighttps','setIsJSRe','supabase-js','migrations',
    'httpsend-server-version','pixelStoreinhardToneMapp',
    'privacyPolicyUrl','M12','recent','mxnnohwp4ztop','DidAppear_cuid2',
    'lcepreparedGesturecordDOMParserializeOrigincrement',
    'wrapMethodindian','ups.com','World','httpmethod','hortcut',
    'botsetintent','frameLightspeedoutrighttps',
    'enableLayoutAnimationsOnAndroidoNotStripQMarkisPageHiddenable',
    'LayoutAnimations','capturePerformance','network','browser',
    'filesystem.local','default.url','dev.to','auspost','zhegan',
    'ghibli','mqcdn','spoqa','ifsg','colors','variable','raster'
}

def scan(path, label):
    if not os.path.exists(path):
        print(f">>> MISSING: {path}")
        return
    print(f"\n===== {label}: {path} =====")
    data = open(path, "rb").read()
    hosts = set()
    # match hostname + optional port + optional path
    # pattern: http(s)://host.tld(:port)?(/path)?
    pat = rb"https?://([a-zA-Z0-9]([a-zA-Z0-9_\-\\.]*[a-zA-Z0-9])?\.[a-zA-Z]{2,})(:\d{1,5})?(/[A-Za-z0-9._~:/?#\[\]@!\$&'()*+\-,;=%]*)?"
    for m in re.finditer(pat, data):
        host = m.group(1).decode("utf-8", "replace").lower()
        port = m.group(2).decode("utf-8", "replace") if m.group(2) else ""
        path_part = m.group(3).decode("utf-8", "replace") if m.group(3) else ""
        if any(skh in host for skh in SKIP_HOSTS):
            continue
        if host.count(".") < 1:
            continue
        h = host
        hosts.add(h)
    for h in sorted(hosts):
        print("  ", h[:120])
    if not hosts:
        print("  (no game-relevant hosts found)")

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    scan(os.path.join(base, "apks/mintpull.apk"), "MintPull")
    scan(os.path.join(base, "apks/outpost.apk"), "CardOutpost")
    scan(os.path.join(base, "tcgp.apk"), "TCGP (fresh pull)")
    scan(os.path.join(base, "outpost-mod.apk"), "Outpost mod")
