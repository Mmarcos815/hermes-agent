import os, re

xml_path = os.path.join(os.path.dirname(__file__), "farm_3phones", "uiauto3.xml")
with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
    xml = f.read()

print(f"File size: {len(xml)} bytes")

# Find the app package
pkgs = set(re.findall(r'package="([^"]*)"', xml))
print(f"Packages: {pkgs}")

# Extract all text
texts = re.findall(r'text="([^"]*)"', xml)
non_empty = [t for t in texts if t.strip()]
print(f"\n=== {len(non_empty)} text elements ===")
for t in non_empty:
    print(repr(t))

# Extract resource-id + text pairs for clickable elements
nodes = re.findall(
    r'<node[^>]*resource-id="([^"]*)"[^>]*text="([^"]*)"[^>]*class="([^"]*)"[^>]*enabled="([^"]*)"[^>]*clickable="([^"]*)"',
    xml
)
print(f"\n=== {len(nodes)} nodes with resource-id+text ===")
for rid, txt, cls, enabled, clickable in nodes:
    if txt.strip() or rid.strip():
        print(f"  id={rid!r} text={txt!r} cls={cls.split('.')[-1]} enabled={enabled} clickable={clickable}")

# Find any visible dropdowns or text fields
print("\n=== Text fields (EditText) ===")
edits = re.findall(r'<node[^>]*class="([^"]*EditText[^"]*)"[^>]*resource-id="([^"]*)"[^>]*text="([^"]*)"[^>]*hint="([^"]*)"', xml)
for cls, rid, txt, hint in edits:
    print(f"  {rid or 'no-id'}: text={txt!r} hint={hint!r}")

print("\n=== Scrollable containers ===")
scrolls = re.findall(r'<node[^>]*class="([^"]*ScrollView[^"]*)"[^>]*resource-id="([^"]*)"', xml)
for cls, rid in scrolls:
    print(f"  {rid or 'no-id'}: {cls.split('.')[-1]}")

# Check the overall hierarchy depth
print(f"\n=== Root node info ===")
root = re.search(r'<node[^>]*resource-id="([^"]*)"[^>]*class="([^"]*)"[^>]*content-desc="([^"]*)"[^>]*package="([^"]*)"', xml)
if root:
    print(f"  resource-id={root.group(1)!r}")
    print(f"  class={root.group(2)!r}")
    print(f"  content-desc={root.group(3)!r}")
    print(f"  package={root.group(4)!r}")
