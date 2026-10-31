import subprocess
import time
import json
import urllib.request
import websocket

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
port = 9222
cmd = [
    chrome_path,
    f"--remote-debugging-port={port}",
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "http://127.0.0.1:8000/"
]

proc = subprocess.Popen(cmd)
try:
    time.sleep(2)
    pages_url = f"http://127.0.0.1:{port}/json"
    with urllib.request.urlopen(pages_url) as res:
        pages = json.loads(res.read().decode())
    
    target_page = next((p for p in pages if p.get("type") == "page"), None)
    if not target_page:
        print("FAIL: No page found!")
        exit(1)
        
    ws_url = target_page["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)
    
    msg_id = 1
    def send_cdp(method, params=None):
        global msg_id
        payload = {"id": msg_id, "method": method, "params": params or {}}
        ws.send(json.dumps(payload))
        msg_id += 1
        
    def recv_until_id(target_id, timeout=8):
        ws.settimeout(timeout)
        start = time.time()
        while time.time() - start < timeout:
            raw = ws.recv()
            data = json.loads(raw)
            if data.get("method") == "Runtime.consoleAPICalled":
                args = [a.get("value", a.get("description", "")) for a in data["params"]["args"]]
                print(f"[CONSOLE {data['params']['type']}]:", *args)
            if data.get("method") == "Runtime.exceptionThrown":
                print(f"[EXCEPTION]:", data["params"]["exceptionDetails"])
            if data.get("id") == target_id:
                return data
        return None

    send_cdp("Runtime.enable")
    send_cdp("Log.enable")
    time.sleep(1)

    def eval_js(expr):
        global msg_id
        cur_id = msg_id
        send_cdp("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        res = recv_until_id(cur_id)
        if res and "result" in res and "result" in res["result"]:
            val = res["result"]["result"]
            if "value" in val:
                return val["value"]
            return val
        return res

    print("\n=== STEP 1: INITIAL STATE ===")
    eval_js("""
    (async () => {
        const start = Date.now();
        while (Date.now() - start < 10000) {
            if (document.readyState === 'complete' && window.openSourcesModal && document.querySelectorAll('.radar-card').length > 0) {
                return true;
            }
            await new Promise(r => setTimeout(r, 150));
        }
        return false;
    })()
    """)
    title = eval_js("document.title")
    initial_cards = eval_js("document.querySelectorAll('.radar-card').length")
    initial_archived = eval_js("document.getElementById('badge-tab-archived').textContent")
    print(f"Title: {title}")
    print(f"Active cards displayed: {initial_cards}")
    print(f"Archive tab badge count: {initial_archived}")

    print("\n=== STEP 2: TEST SOURCES BUTTON CLICK ===")
    res_sources = eval_js("""
    (async () => {
        const btn = document.getElementById('btn-open-sources');
        btn.click();
        await new Promise(r => setTimeout(r, 600));
        const modal = document.getElementById('sources-modal');
        const rows = modal.querySelectorAll('tbody tr').length;
        const display = window.getComputedStyle(modal).display;
        const healthyCount = document.getElementById('modal-stat-healthy').textContent;
        return {
            modalVisible: display === 'flex' && !modal.classList.contains('hidden'),
            rowsCount: rows,
            healthyBadge: healthyCount
        };
    })()
    """)
    print("Sources Modal State:", res_sources)
    assert res_sources["modalVisible"] == True, "FAIL: Sources modal did not become visible!"
    assert res_sources["rowsCount"] >= 20, f"FAIL: Expected >= 20 rows, got {res_sources['rowsCount']}"

    print("\n=== STEP 3: CLOSE SOURCES MODAL ===")
    res_close = eval_js("""
    (() => {
        document.getElementById('btn-close-sources').click();
        const modal = document.getElementById('sources-modal');
        const display = window.getComputedStyle(modal).display;
        return { isClosed: display === 'none' || modal.classList.contains('hidden') };
    })()
    """)
    print("Sources Closed:", res_close)
    assert res_close["isClosed"] == True, "FAIL: Sources modal did not close!"

    print("\n=== STEP 4: TEST ARCHIVE BUTTON ON CARD ===")
    res_archive_card = eval_js("""
    (async () => {
        const btnArchive = document.querySelector('.btn-card-archive');
        if (!btnArchive) return { error: 'No .btn-card-archive found' };
        btnArchive.click();
        await new Promise(r => setTimeout(r, 500));
        const toasts = document.querySelectorAll('.radar-toast');
        const lastToastText = toasts.length > 0 ? toasts[toasts.length - 1].textContent.trim() : 'no toast';
        const badgeCount = document.getElementById('badge-tab-archived').textContent;
        return {
            archivedClicked: true,
            toastText: lastToastText,
            badgeCount: badgeCount
        };
    })()
    """)
    print("Archive Card Result:", res_archive_card)
    assert "Archived" in res_archive_card.get("toastText", ""), "FAIL: No archive toast shown!"

    print("\n=== STEP 5: SWITCH TO ARCHIVE TAB & RESTORE ===")
    res_tab_archive = eval_js("""
    (async () => {
        const tab = document.querySelector('[data-feed=\"archived\"]');
        tab.click();
        await new Promise(r => setTimeout(r, 600));
        const archiveCards = document.querySelectorAll('.radar-card').length;
        const restoreBtns = document.querySelectorAll('.btn-card-restore').length;
        
        // Click restore on first archived card
        const firstRestore = document.querySelector('.btn-card-restore');
        if (firstRestore) {
            firstRestore.click();
            await new Promise(r => setTimeout(r, 500));
        }
        const toasts = document.querySelectorAll('.radar-toast');
        const lastToastText = toasts.length > 0 ? toasts[toasts.length - 1].textContent.trim() : 'no toast';
        const updatedBadge = document.getElementById('badge-tab-archived').textContent;

        return {
            archiveCardsBefore: archiveCards,
            restoreBtnsBefore: restoreBtns,
            restoreToast: lastToastText,
            updatedBadge: updatedBadge
        };
    })()
    """)
    print("Archive Tab & Restore Result:", res_tab_archive)
    assert "Restored" in res_tab_archive.get("restoreToast", ""), "FAIL: No restore toast shown!"

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")
    ws.close()
finally:
    proc.terminate()
