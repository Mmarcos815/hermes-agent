import re, os

xml_path = os.path.join(os.path.dirname(__file__), "farm_3phones", "uiauto3.xml")
with open(xml_path, "r", encoding="utf-8", errors="replace") as f:
    xml = f.read()

print(f"XML size: {len(xml)} bytes")

# Find ALL nodes with text or content-desc
print("\n=== Nodes with non-empty text or content-desc ===")
count = 0
for m in re.finditer(r'<node\b([^>]+)>', xml):
    attrs = m.group(1)
    text_m = re.search(r'text="([^"]*)"', attrs)
    desc_m = re.search(r'content-desc="([^"]*)"', attrs)
    rid_m = re.search(r'resource-id="([^"]*)"', attrs)
    cls_m = re.search(r'class="([^"]*)"', attrs)
    bounds_m = re.search(r'bounds="([^"]*)"', attrs)
    clickable_m = re.search(r'clickable="([^"]*)"', attrs)
    text = text_m.group(1) if text_m else ""
    desc = desc_m.group(1) if desc_m else ""
    rid = rid_m.group(1) if rid_m else ""
    cls = cls_m.group(1) if cls_m else ""
    bounds = bounds_m.group(1) if bounds_m else ""
    clickable = clickable_m.group(1) if clickable_m else "false"
    
    if text.strip() or desc.strip():
        count += 1
        print(f"[{count}] bounds={bounds} text={text!r} desc={desc!r} rid={rid!r} cls={cls.split('.')[-1] if '.' in cls else cls} clickable={clickable}")

print(f"\nTotal text/desc nodes: {count}")

# Also dump full XML structure around any node with text
print("\n=== Snippet around each text node ===")
for m in re.finditer(r'<node\b([^>]+)>', xml):
    attrs = m.group(1)
    text_m = re.search(r'text="([^"]*)"', attrs)
    desc_m = re.search(r'content-desc="([^"]*)"', attrs)
    if text_m and text_m.group(1).strip():
        start = max(0, m.start() - 20)
        end = min(len(xml), m.end() + 200)
        print(f"\n--- Match at pos {m.start()} ---")
        print(xml[start:end][:400])
        print()
