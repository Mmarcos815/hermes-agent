'use strict';
// TCGP Frida bypass — find SlicerView and call OnSwipeComplete

Java.perform(() => {
    const UnityPlayerActivity = Java.use('com.unity3d.player.UnityPlayerActivity');
    const activity = Java.use('android.app.Activity');
    const mainThread = Java.use('android.os.Looper').mainLooper.getQueue();
    
    console.log('Activity: ' + Java.use('com.unity3d.player.UnityPlayerActivity').class.getName());
});

const il2cpp = Process.findModuleByName('libil2cpp.so');
console.log('il2cpp base: ' + il2cpp.base);

// Search for SlicerView type - hook MonoBehaviour.findObjectsOfType
setTimeout(() => {
    // Try to find objects using Resources.FindObjectsOfTypeAll
    const FindObjectsOfTypeAll = il2cpp.getExportByName('il2cpp_resolve_icall');
    
    // Hook Object.Find to find active GameObjects
    const GameObject = il2cpp.getExportByName('il2cpp_class_from_name');
    
    console.log('Frida TCGP bypass active, scanning for SlicerView...');
}, 1000);
