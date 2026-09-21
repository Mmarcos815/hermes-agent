'use strict';
// Bypass TCGP pack swipe by calling SlicerView.OnSwipeComplete directly

function bypassSwipe() {
    Java.perform(() => {
        const ActivityThread = Java.use('android.app.ActivityThread');
        const activityThread = ActivityThread.currentActivityThread();
        const activities = activityThread.mActivities.value;
        
        for (let i = 0; i < activities.size(); i++) {
            const record = activities.value[i];
            if (record) {
                const activity = record.activity.value;
                const name = activity.getClass().getName();
                console.log('Activity[' + i + ']: ' + name);
            }
        }
    });

    // Hook SlicerView to detect swipe state
    const il2cpp = Process.findModuleByName('libil2cpp.so');
    if (!il2cpp) { console.log('no il2cpp'); return; }

    // Find SlicerView via il2cpp - need to get the domain, assembly, image, class
    // This requires il2cpp runtime functions
    const il2cpp_domain_get = new NativeFunction(il2cpp.getExportByName('il2cpp_domain_get'), 'pointer', []);
    const il2cpp_domain_assembly_open = new NativeFunction(il2cpp.getExportByName('il2cpp_domain_assembly_open'), 'pointer', ['pointer', 'pointer']);
    const il2cpp_class_from_name = new Function(il2cpp.getExportByName('il2cpp_class_from_name'), 'pointer', ['pointer', 'pointer', 'pointer']);
    
    // We can try to hook MonoBehaviour.update to find active slicer
    console.log('il2cpp base: ' + il2cpp.base);
    
    // Find SlicerView$RVA for methods - need script.json offsets
    // SlicerView::OnSwipeComplete RVA from dump.cs - search script.json
    // For now, try to find the class via the runtime
    
    // Alternative: hook Unity's MonoBehaviour to find all instances
    const GameObject = Java.use('com.unity3d.player.UnityPlayer');
    console.log('Bypass script loaded');
}

setTimeout(bypassSwipe, 2000);
