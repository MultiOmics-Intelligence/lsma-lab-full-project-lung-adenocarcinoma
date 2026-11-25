# Mutation frequencies of lung adenocarcinoma genes in independent cBioPortal cohorts (public API, read-only).
import csv, json, subprocess, sys
API = "https://www.cbioportal.org/api"
GENES = ["TP53", "KRAS", "EGFR", "STK11", "KEAP1", "SMARCA4", "NF1", "BRAF", "PIK3CA", "RBM10", "ARID1A", "SETD2", "ATM", "CDKN2A", "U2AF1", "MET", "ERBB2", "MGA", "RB1", "APC",
         "TTN", "MUC16", "CSMD3", "RYR2", "LRP1B", "ZFHX4", "USH2A", "SPTA1", "XIRP2"]
def get(url, data=None):
    cmd = ["curl", "-s", "-m", "120", "-H", "Content-Type: application/json", "-H", "Accept: application/json"]
    if data is not None: cmd += ["-X", "POST", "--data", json.dumps(data)]
    return json.loads(subprocess.run(cmd + [url], capture_output=True, text=True).stdout)
genes = get(API + "/genes/fetch?geneIdType=HUGO_GENE_SYMBOL", GENES)
eid = {g["hugoGeneSymbol"]: g["entrezGeneId"] for g in genes}
out = {}
for study in sys.argv[1:]:
    sl = get(f"{API}/sample-lists/{study}_sequenced")
    n = len(sl.get("sampleIds", []))
    muts = get(f"{API}/molecular-profiles/{study}_mutations/mutations/fetch?projection=SUMMARY",
               {"sampleListId": f"{study}_sequenced", "entrezGeneIds": list(eid.values())})
    by = {}
    for m in muts:
        if m.get("mutationType") in ("Silent", "Intron", "3'UTR", "5'UTR", "RNA", "IGR", "3'Flank", "5'Flank"): continue
        by.setdefault(m["entrezGeneId"], set()).add(m["sampleId"])
    out[study] = {"n": n, "counts": {g: len(by.get(e, ())) for g, e in eid.items()}}
    print(study, n, {g: round(100 * len(by.get(e, ())) / max(n, 1), 1) for g, e in list(eid.items())[:10]})
json.dump(out, open("independent_cohorts.json", "w"), indent=1)
