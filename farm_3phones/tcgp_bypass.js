'use strict';
// TCGP pack opening bypass — invoke Unity C# method directly

function hookTCGP() {
    const il2cpp = Process.findModuleByName('libil2cpp.so');
    if (!il2cpp) { console.log('no il2cpp'); return; }
    
    // Try to find common OpenPack method names via reflection
    Java.perform(() => {
        try {
            const UnityPlayer = Java.use('com.unity3d.player.UnityPlayerActivity');
            // Try to send message to Unity
            // Unity C# side: public void SendMessage(string methodName, string value)
            console.log('UnityPlayerActivity found: ' + UnityPlayer.class.getName());
        } catch(e) {}
    });

    // Try to send Unity message via activity
    try {
        const activity = Java.use('com.unity3d.player.UnityPlayer');
        console.log('UnityPlayer found');
    } catch(e) {}

    console.log('il2cpp base: ' + il2cpp.base);
}

hookTCGP();
