// rewards: client-side grant evaluation hooks (read-only)
send("[rewards ready]");
var _m = Process.findModuleByName("libil2cpp.so");
var base = _m.base;
function hook(rva, name, cb) {
    try {
        Interceptor.attach(base.add(rva), { onEnter: function (args) { try { cb(args); } catch (e) {} } });
        send("[rewards] hooked " + name);
    } catch (e) { send("[rewards] fail " + name + ": " + e); }
}
// DailyLoginPopUp.PresentClaimReward(DailyLoginClaimResult): ClaimedDay int @+0x10
hook(0x2225128, "PresentClaimReward", function (args) {
    var day = args[1].add(0x10).readS32();
    send("[grant] daily ClaimedDay=" + day);
});
// GiftCodePopUp.ClaimPack(JToken): log token type pointer
hook(0x22FB178, "ClaimPack", function (args) {
    send("[grant] ClaimPack jtoken=" + args[1]);
});
send("[rewards armed]");
