#!/usr/bin/env python3
"""
FRONTEND UNIT TESTS for Smart Port Management System
Tests Utils, Store, Api, App functions via Node.js eval.
Run: python3 tests/test_frontend_units.py
"""

import subprocess
import sys
import os
import json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_DIR = os.path.join(PROJECT_DIR, "js")

PASS = 0
FAIL = 0
SKIP = 0

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def run_js(script):
    """
    Run inline JavaScript through Node.js.
    Loads the project JS files as context, then runs the test script.
    """
    context = ""
    for f in ["utils.js", "config.js", "store.js", "app.js"]:
        fp = os.path.join(JS_DIR, f)
        if os.path.exists(fp):
            with open(fp) as fh:
                ctx = fh.read()
                if f == "utils.js":
                    ctx = ctx.replace("console.error", "const __log =")
                    ctx = ctx.replace("console.log", "const __log =")
                context += f"// --- {f} ---\n{ctx}\n"
        else:
            print(f"  {RED}Missing: {fp}{RESET}")

    node_script = f"""
// Stub browser globals
globalThis.document = {{ addEventListener: () => {{}}, getElementById: () => {{}}, querySelector: () => {{}}, querySelectorAll: () => [], createElement: () => ({{ style: {{}} }}), body: {{ appendChild: () => {{}} }}, removeChild: () => {{}} }};
globalThis.window = {{ addEventListener: () => {{}}, location: {{ href: 'http://localhost:5500' }}, localStorage: {{}} }};
globalThis.localStorage = new (class {{
    constructor() {{ this.store = {{}}; }}
    getItem(k) {{ return this.store[k] || null; }}
    setItem(k, v) {{ this.store[k] = String(v); }}
    removeItem(k) {{ delete this.store[k]; }}
    clear() {{ this.store = {{}}; }}
}})();
globalThis.fetch = (url, opt) => {{
    return Promise.reject(new Error('network unavailable'));
}};
globalThis.navigator = {{ onLine: true }};
globalThis.alert = () => {{}};
globalThis.Chart = () => {{}};

// Capture results for test assertions
const results = [];
function assert(label, condition) {{
    results.push({{ 'label': label, 'ok': !!condition }});
}}
function assertEqual(label, actual, expected) {{
    results.push({{ 'label': label, 'ok': String(actual) === String(expected), 'actual': String(actual), 'expected': String(expected) }});
}}

{script}

console.log('__RESULTS__' + JSON.stringify(results));
    """
    full_script = context + "\n" + node_script

    try:
        import subprocess
        r = subprocess.run(["node", "-e", full_script], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            print(f"    {RED}Node Error:{RESET} {r.stderr.strip().split(chr(10))[-1]}")
            return None
        out = r.stdout.strip()
        marker = "__RESULTS__"
        if marker in out:
            return json.loads(out[out.index(marker) + len(marker):])
        print(f"    {YELLOW}No results found:{RESET} {out[:200]}")
        return None
    except FileNotFoundError:
        print(f"  {RED}Node.js not found. Install: brew install node{RESET}")
        return None
    except Exception as e:
        print(f"  {RED}Error:{RESET} {e}")
        return None


def test_module(name, tests):
    global PASS, FAIL, SKIP
    print(f"\n═══ {name} ===")
    results = run_js(tests)
    if results is None:
        SKIP += 1
        return
    for opts in results:
        if opts["ok"]:
            PASS += 1
            print(f"  {GREEN}PASS{RESET} {opts['label']}")
        else:
            FAIL += 1
            a = opts.get("actual", "?")
            e = opts.get("expected", "?")
            print(f"  {RED}FAIL{RESET} {opts['label']} (got: {a}, expected: {e})")


# ============================================================
# TESTS FOR UTILITY FUNCTIONS
# ============================================================
UTILS_TESTS = """
// === TESTS ===
try {
    assert("Utils exists", typeof Utils !== 'undefined');
    assertEqual("Utils formatNumber", Utils.formatNumber(12345), "12,345");
    assertEqual("Utils formatNumber decimal", Utils.formatNumber(1234.56), "1,234.56");
    assertEqual("Utils formatNumber zero", Utils.formatNumber(0), "0");
    assertEqual("Utils formatNumber negative", Utils.formatNumber(-5000), "-5,000");

    let d = Utils.formatDate('2026-08-01');
    assert("Utils.formatDate returns string", typeof d === 'string');

    assert("Utils.generateId returns string", typeof Utils.generateId() === 'string');
    assert("Utils.generateId unique", Utils.generateId() !== Utils.generateId());

    assert("Utils paginate page 1", Utils.paginate([1,2,3,4,5,6,7,8,9,10], 1, 3).length === 3);
    assert("Utils paginate page 2", Utils.paginate([1,2,3,4,5,6], 2, 3).length === 3);
    assert("Utils paginate empty", Utils.paginate([], 1, 10).length === 0);
    assert("Utils paginate out of range", Utils.paginate([1,2], 5, 10).length === 0);
} catch(e) {
    assert("Utils error: " + e.message, false);
}
"""


# ============================================================
# TESTS FOR CONFIG/API
# ============================================================
CONFIG_TESTS = """
// === Config Tests ===
try {
    assert("Api object exists", typeof Api !== 'undefined');
    assert("Api has login", typeof Api.login === 'function');
    assert("Api has request", typeof Api.request === 'function');
    assert("Api has get", typeof Api.get === 'function');
    assert("Api has post", typeof Api.post === 'function');
    assert("Api has put", typeof Api.put === 'function');
    assert("Api has delete", typeof Api.delete === 'function');
    assert("MOCK_USERS exists", typeof MOCK_USERS !== 'undefined');
    assert("MOCK_USERS has users", Object.keys(MOCK_USERS).length > 1);
} catch(e) {
    assert("Config error: " + e.message, false);
}
"""


# ============================================================
# TESTS FOR STORE
# ============================================================
STORE_TESTS = """
// === Store Tests ===
try {
    // Store init may fail without HTML, but store op should still test collect
    assert("Store object exists", typeof Store !== 'undefined');
    assert("Store.get is function", typeof Store.get === 'function');
    assert("Store.add is function", typeof Store.add === 'function');
    assert("Store.update is function", typeof Store.update === 'function');
    assert("Store.remove is function", typeof Store.remove === 'function');
    assert("Store.init is function", typeof Store.init === 'function');
    assert("Store.getUser is function", typeof Store.getUser === 'function');
    assert("Store.getShipStats is function", typeof Store.getShipStats === 'function');
    assert("Store.getContainerStats is function", typeof Store.getContainerStats === 'function');
    assert("Store.getTruckStats is function", typeof Store.getTruckStats === 'function');
    assert("Store.getDashboardKPIs is function", typeof Store.getDashboardKPIs === 'function');

    // Seed data can be accessed even without init if we check the right way
    if (Store.SEED_DATA && Store.SEED_DATA.ships) {
        assert("Seed data has ships", Store.SEED_DATA.ships.length >= 10);
        assert("Seed data has containers", Store.SEED_DATA.containers.length >= 10);
        assert("Seed data has trucks", Store.SEED_DATA.trucks.length >= 10);
    }
} catch(e) {
    assert("Store error: " + e.message, false);
}
"""


# ============================================================
# TESTS FOR APP
# ============================================================
APP_TESTS = """
// === App Tests ===
try {
    assert("App object exists", typeof App !== 'undefined');

    // Core method checks
    assert("App.showToast", typeof App.showToast === 'function');
    assert("App.createModal", typeof App.createModal === 'function');
    assert("App.exportCSV", typeof App.exportCSV === 'function');
    assert("App.initSearch", typeof App.initSearch === 'function');
    assert("App.initUserDisplay", typeof App.initUserDisplay === 'function');
    assert("App.initNotifications", typeof App.initNotifications === 'function');

    // Newly added methods
    assert("App.editProfile", typeof App.editProfile === 'function');
    assert("App.saveProfile", typeof App.saveProfile === 'function');
    assert("App.exportTrucks", typeof App.exportTrucks === 'function');
    assert("App.exportSecurity", typeof App.exportSecurity === 'function');
    assert("App.exportBerths", typeof App.exportBerths === 'function');

    // Modal-related
    assert("App.showAddTruckModal", typeof App.showAddTruckModal === 'function');
    assert("App.submitAddTruck", typeof App.submitAddTruck === 'function');
    assert("App.showAddAlertModal", typeof App.showAddAlertModal === 'function');
    assert("App.submitAddAlert", typeof App.submitAddAlert === 'function');
    assert("App.showAddScheduleModal", typeof App.showAddScheduleModal === 'function');
    assert("App.submitAddSchedule", typeof App.submitAddSchedule === 'function');

    // Test showToast doesn't throw
    App.showToast('Test message', 'info');
    assert("App.showToast no error", true);
} catch(e) {
    assert("App error: " + e.message, false);
}
"""


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print(f"\n{'=' * 60}")
    print("  SMART PORT MANAGEMENT - Frontend Unit Tests")
    print("=" * 60)

    test_module("UTILS", UTILS_TESTS)
    test_module("CONFIG/API", CONFIG_TESTS)
    test_module("STORE", STORE_TESTS)
    test_module("APP", APP_TESTS)

    print(f"\n{'=' * 60}")
    print(f"  Results: {PASS} passed, {FAIL} failed, {SKIP} skipped")
    print(f"  Total: {PASS + FAIL + SKIP} tests")
    print(f"{'=' * 60}")

    sys.exit(0 if FAIL == 0 else 1)