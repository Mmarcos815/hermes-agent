import os, re

xml = open("farm_3phones/uiauto3.xml", "r", encoding="utf-8", errors="replace").read()

# Find all nodes with bounds
print("=== Nodes with bounds + text/content-desc ===")
for m in re.finditer(
    r'<node[^>]*bounds="(\[[0-9]+,\s*[0-9]+,\s*[0-9]+,\s*[0-9]+\])"[^>]*'
    r'(?:text="([^"]*)"[^>]*)?'
    r'(?:content-desc="([^"]*)"[^>]*)?'
    r'(?:resource-id="([^"]*)"[^>]*)?'
    r'(?:class="([^"]*)"[^>]*)?',
    xml
):
    bounds = m.group(1)
    text = m.group(2) or ""
    desc = m.group(3) or ""
    rid = m.group(4) or ""
    cls = m.group(5) or ""
    if text.strip() or desc.strip() or rid.strip():
        print(f"bounds={bounds} text={text!r} desc={desc!r} rid={rid!r} class={cls.split('.')[-1] if '.' in cls else cls}")

# Also find all nodes that are clickable
print("\n=== Clickable nodes ===")
for m in re.finditer(
    r'<node[^>]*clickable="true"[^>]*bounds="(\[[0-9,\s]+\])"'
    r'([^>]*?)(/?)>',
    xml
):
    bounds = m.group(1)
    attrs = m.group(2)
    text_m = re.search(r'text="([^"]*)"', attrs)
    rid_m = re.search(r'resource-id="([^"]*)"', attrs)
    desc_m = re.search(r'content-desc="([^"]*)"', attrs)
    cls_m = re.search(r'class="([^"]*)"', attrs)
    text = text_m.group(1) if text_m else ""
    rid = rid_m.group(1) if rid_m else ""
    desc = desc_m.group(1) if desc_m else ""
    cls = cls_m.group(1) if cls_m else ""
    if text.strip() or desc.strip() or rid.strip():
        print(f"bounds={bounds} text={text!r} desc={desc!r} rid={rid!r} class={cls.split('.')[-1] if '.' in cls else cls}")

print("\n=== Bottom nav nodes ===")
for m in re.finditer(
    r'<node[^>]*bounds="(\[[0-9,\s]+\])"[^>]*class="([^"]*)[Nn]avigation[^"]*"',
    xml
):
    print(f"bounds={m.group(1)} class={m.group(2)}")

print("\n=== All nodes with class containing 'Button|Spinner|Switch|Toggle|App' ===")
for m in re.finditer(
    r'<node[^>]*class="([^"]*)"[^>]*bounds="(\[[0-9,\s]+\])"[^>]*text="([^"]*)"',
    xml
):
    cls = m.group(1)
    bounds = m.group(2)
    text = m.group(3)
    if any(k in cls.lower() for k in ["button", "spinner", "switch", "toggle", "app", "image"]):
        if text.strip():
            print(f"class={cls.split('.')[-1]} bounds={bounds} text={text!r}")
