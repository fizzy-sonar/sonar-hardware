import json, subprocess, sys, urllib.request, os

DEST = "/private/tmp/sonar-t017/spikes/eda-zener/deep-port/sonar_v1_deep_port/components/registry"
PARTS = [  # (mpn, manufacturer, prefer)
    ("OPA4171AIDR", "Texas Instruments", "lcsc"),
    ("AP63301WU-7", "Diodes Incorporated", "both"),
    ("DRV8876PWPR", "Texas Instruments", "both"),
]

def search(mpn):
    p = subprocess.run(["pcb","component","search",mpn,"--format","json","--limit","3"],
                       capture_output=True, text=True, timeout=90)
    rows = json.loads(p.stdout)
    for r in rows:
        if r.get("mpn","").lower()==mpn.lower(): return r
    return rows[0] if rows else None

def dl(mpn, mfr, key, ident):
    args = ["pcb","component","download","--mpn",mpn,"--manufacturer",mfr,"--format","json"]
    if key=="cse": args += ["--cse-part-ref", ident]
    else: args += ["--lcsc-part-number", ident]
    p = subprocess.run(args, capture_output=True, text=True, timeout=180)
    try: return json.loads(p.stdout)
    except Exception: return {"error": (p.stdout+p.stderr)[:300]}

os.makedirs(DEST, exist_ok=True)
for mpn, mfr, pref in PARTS:
    r = search(mpn)
    cse_ref = (r.get("cse") or {}).get("part_ref")
    lcsc_no = (r.get("lcsc") or {}).get("part_number")
    d = os.path.join(DEST, mpn); os.makedirs(d, exist_ok=True)
    order = ["lcsc","cse"] if pref=="lcsc" else ["cse","lcsc"]
    got = {}
    for backend in order:
        if backend=="cse" and not cse_ref: continue
        if backend=="lcsc" and not lcsc_no: continue
        if pref=="lcsc" and got: break
        res = dl(mpn, mfr, backend, cse_ref if backend=="cse" else lcsc_no)
        blk = res.get(backend) or {}
        if "error" in res or not blk:
            print(f"{mpn} {backend}: FAIL {str(res)[:160]}"); continue
        for kind in ("symbol_url","footprint_url","step_url"):
            url = blk.get(kind)
            if not url: continue
            ext = ".kicad_sym" if "sym" in kind else (".kicad_mod" if "foot" in kind else ".step")
            fn = os.path.join(d, f"{backend}{ext}")
            urllib.request.urlretrieve(url, fn)
            got.setdefault(backend, []).append(fn)
        print(f"{mpn} {backend}: got {list(blk.keys())}")
    # stop after first successful backend if pref==both? no: 'both' means try both
json.dump("done", open("/tmp/fetch_done.json","w"))
