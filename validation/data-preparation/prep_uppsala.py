# Uppsala NSCLC cohort (GSE81089): keep lung adenocarcinomas (histology code 2) and the normal lung samples;
# NCBI-computed raw counts (GRCh38) with gene symbols from NCBI gene_info; a sample sheet in the lab's format.
import csv, gzip, re, sys
from datetime import date
txt = open("GSE81089_gsm.txt").read()
STAGE = {"1": "Stage I", "2": "Stage I", "3": "Stage II", "4": "Stage II", "5": "Stage III", "6": "Stage III", "7": "Stage IV"}
SMOKE = {"1": "current", "2": "former", "3": "never"}
sheet = {}
for b in txt.split("^SAMPLE = ")[1:]:
    gsm = b.split("\n")[0].strip()
    ch = dict(re.findall(r"!Sample_characteristics_ch1 = ([^:]+): (.*)", b))
    code = ch["tumor (t) or normal (n)"].strip()
    if code.endswith("N"):
        sheet[gsm] = dict(sample_id=gsm, patient=code[:-1], tissue="normal", stage="", vital_status="", survival_days="", gender="", age="", smoking="", histology="normal lung")
    elif ch.get("histology") == "2":
        d = lambda s: date.fromisoformat(s.strip())
        try: days = (d(ch["vital date"]) - d(ch["surgery date"])).days
        except Exception: days = ""
        dead = ch.get("dead", "").strip()
        sheet[gsm] = dict(sample_id=gsm, patient=code[:-1], tissue="tumour", stage=STAGE.get(ch.get("stage tnm", "").strip(), ""),
                          vital_status={"1": "Dead", "0": "Alive"}.get(dead, ""), survival_days=days, gender=ch.get("gender", ""), age=ch.get("age", ""),
                          smoking=SMOKE.get(ch.get("smoking", "").strip(), ""), histology="adenocarcinoma")
sym = {}
with gzip.open("gene_info.gz", "rt") as f:
    next(f)
    for line in f:
        p = line.split("\t"); sym[p[1]] = p[2]
with gzip.open("GSE81089_counts.tsv.gz", "rt") as f, gzip.open("uppsala/GSE81089_LUAD_counts.tsv.gz", "wt") as out:
    head = next(f).rstrip("\n").split("\t")
    keep = [i for i, g in enumerate(head) if g in sheet]
    out.write("\t".join(["gene_id", "gene_name"] + [head[i] for i in keep]) + "\n")
    for line in f:
        p = line.rstrip("\n").split("\t")
        out.write("\t".join([p[0], sym.get(p[0], p[0])] + [p[i] for i in keep]) + "\n")
cols = ["sample_id", "patient", "tissue", "stage", "vital_status", "survival_days", "gender", "age", "smoking", "histology"]
with open("uppsala/GSE81089_LUAD_sample_sheet.tsv", "w") as f:
    w = csv.DictWriter(f, cols, delimiter="\t"); w.writeheader()
    for gsm in head[1:]:
        if gsm in sheet: w.writerow(sheet[gsm])
t = [r for r in sheet.values() if r["tissue"] == "tumour"]; n = [r for r in sheet.values() if r["tissue"] == "normal"]
print("tumours", len(t), "normals", len(n), "paired normals", sum(r["patient"] in {x["patient"] for x in t} for r in n))
from collections import Counter
print(Counter(r["stage"] for r in t), Counter(r["vital_status"] for r in t), "missing days", sum(r["survival_days"] == "" for r in t))
