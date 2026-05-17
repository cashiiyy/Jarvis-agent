"""Full integration test for all v5 modules."""
import sys
sys.path.insert(0, ".")

from core.active_device_manager import get_device_manager
from core.intent_classifier import classify, Intent
from core.command_parser import parse
from core.context_memory import get_memory

P=0; F=0
def chk(label, got, exp):
    global P,F
    ok=(got==exp)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:<50s} got={got!r}")
    if ok: P+=1
    else: F+=1

print("\n=== Active Device Manager ===")
mgr = get_device_manager()
chk("default=phone",                 mgr.active, "phone")
chk("set phone",                     mgr.set_device("phone"),   "phone")
chk("set laptop",                    mgr.set_device("laptop"),  "laptop")
chk("set android",                   mgr.set_device("android"), "phone")
chk("detect 'switch to tablet'",     mgr.detect_set_command("switch to tablet"), "tablet")
chk("detect 'set default to phone'", mgr.detect_set_command("set default to phone"), "Android phone")
chk("is_query 'current device'",     mgr.is_query("what is the current device"), True)
chk("is_query 'open chrome'",        mgr.is_query("open chrome"), False)

print("\n=== Intent Classifier ===")
chk("DEVICE_SWITCH - switch to phone",     classify("switch to phone").value,  "DEVICE_SWITCH")
chk("DEVICE_QUERY  - current device",      classify("what is the current device").value, "DEVICE_QUERY")
chk("SEND_MESSAGE  - send hi to mummy",    classify("send hi to mummy").value, "SEND_MESSAGE")
chk("OPEN_APP      - open whatsapp",       classify("open whatsapp").value,    "OPEN_APP")
chk("SEARCH        - search lofi music",   classify("search lofi music").value,"SEARCH")
chk("MULTISTEP     - open wa and send...", classify("open whatsapp and send hi to mom").value, "MULTISTEP")

print("\n=== Command Parser ===")
c = parse("send hello to mummy on phone")
chk("send: action=send",       c.action,        "send")
chk("send: message=hello",     c.message_body,  "hello")
chk("send: contact=mummy",     c.contact_name,  "mummy")
chk("send: device=phone",      c.device_target, "phone")

c2 = parse("open youtube on my tablet")
chk("open: action=open",       c2.action,       "open")
chk("open: app=youtube",       c2.app_target,   "youtube")
chk("open: device=tablet",     c2.device_target,"tablet")

c3 = parse("open whatsapp and send hi to mummy")
chk("multi: steps=2",          len(c3.steps),   2)

print("\n=== Context Memory ===")
mem = get_memory()
mem.update(app="whatsapp", device="phone", contact="mummy")
app, dev, contact, q = mem.fill_gaps()
chk("mem: fill app",           app,     "whatsapp")
chk("mem: fill device",        dev,     "phone")
chk("mem: fill contact",       contact, "mummy")
# Override with explicit
app2, _, _, _ = mem.fill_gaps(app="youtube")
chk("mem: explicit overrides", app2,    "youtube")

print(f"\n{'='*50}\n  PASSED:{P}  FAILED:{F}\n{'All PASS' if F==0 else 'FAILURES'}\n{'='*50}")
sys.exit(0 if F==0 else 1)
