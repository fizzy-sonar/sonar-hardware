import json, subprocess, sys

MPNS = [
 # key ICs / modules
 "AP63301WU-7","TPS55340PWPR","CDCLVC1112PWR","LAN8720A","ICS-41352",
 "ICS-41350","DRV8876PWPR","FT232HL-TRAY","OPA4171AIDR","SPH0641LU4H-1",
 "HR911105A","SG-8002CA","SS34","PSPHAQ127-270M","AO3415","DZDH0401DW-7",
 "BLM18KG121TN1D","1935161",
 # passives (sheet MPNs)
 "RC0603FR-0710KL","RC0603FR-07100KL","CC0603KRX7R9BB104","CL10A105KB8NNNC",
 "CL10A106MA8NRNC","CL10B472KB8NNNC","CL10B473KB8NNNC","GRM188C61E226ME01D",
 "0603WAF8662T5E","FRC0603F1691TS","FRC0603F7872TS",
]

def assets(r):
    cse = r.get("cse") or {}
    lc = r.get("lcsc") or {}
    s = bool(cse.get("symbol")); f = bool(cse.get("footprint")); st = bool(cse.get("step"))
    ls = bool(lc.get("symbol")); lf = bool(lc.get("footprint")); lst = bool(lc.get("step"))
    return s,f,st,ls,lf,lst

out = []
for mpn in MPNS:
    try:
        p = subprocess.run(["pcb","component","search",mpn,"--format","json","--limit","5"],
                           capture_output=True, text=True, timeout=60)
        rows = json.loads(p.stdout) if p.returncode==0 and p.stdout.strip() else []
    except Exception as e:
        out.append((mpn,"ERROR:"+str(e),None)); continue
    exact = [r for r in rows if r.get("mpn","").lower()==mpn.lower()]
    r = (exact or rows or [None])[0]
    if r is None:
        out.append((mpn,"no-hit",None)); continue
    s,f,st,ls,lf,lst = assets(r)
    tag = "exact" if exact else "near:"+r.get("mpn","?")
    a = []
    if s or f or st: a.append("cse:"+"".join(x for x,b in zip("SF3",(s,f,st)) if b))
    if ls or lf or lst: a.append("lcsc:"+"".join(x for x,b in zip("SF3",(ls,lf,lst)) if b))
    out.append((mpn, tag, ",".join(a) if a else "no-assets"))

for mpn, tag, a in out:
    print(f"{mpn:22s} {tag:28s} {a or '-'}")
json.dump(out, open("/private/tmp/sonar-t017/spikes/eda-zener/deep-port/coverage/results.json","w"), indent=1)
