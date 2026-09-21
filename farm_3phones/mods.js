// list native modules (read-only)
var names = [];
Process.enumerateModules().forEach(function (m) { names.push(m.name); });
send("[mods] " + JSON.stringify(names));
send("[mods done]");
