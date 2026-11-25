# Oslo lung adenocarcinoma methylation cohort (GSE66836, 450K): beta values from the GEO series matrix, rounded to
# 3 decimals, and a sample sheet with tissue, stage, sex and EGFR/KRAS/TP53 status. No patient pairing is given.
import gzip, csv, re
src = "GSE66836_series_matrix.txt.gz"
meta, ch = {}, []
with gzip.open(src, "rt") as f:
    for line in f:
        if line.startswith("!Sample_geo_accession"): gsm = [x.strip('"') for x in line.rstrip("\n").split("\t")[1:]]
        elif line.startswith("!Sample_title"): title = [x.strip('"') for x in line.rstrip("\n").split("\t")[1:]]
        elif line.startswith("!Sample_characteristics_ch1"): ch.append([x.strip('"') for x in line.rstrip("\n").split("\t")[1:]])
        elif line.startswith("!series_matrix_table_begin"): break
    rows = []
    STAGE = {"1": "Stage I", "2": "Stage I", "3": "Stage II", "4": "Stage II", "5": "Stage III", "6": "Stage III", "7": "Stage IV"}
    for i, g in enumerate(gsm):
        d = dict(c[i].split(": ", 1) for c in ch if ": " in c[i])
        tis = "tumour" if d.get("tissue") == "Tumor" else "normal"
        rows.append({"sample_id": g, "title": title[i], "tissue": tis, "gender": d.get("gender", "").lower(),
                     "stage": STAGE.get(d.get("Stage", ""), "") if tis == "tumour" else "",
                     "egfr": d.get("egfr status", "NA"), "kras": d.get("kras status", "NA"), "tp53": d.get("p53 status", "NA")})
    with open("oslo/GSE66836_sample_sheet.tsv", "w") as o:
        w = csv.DictWriter(o, list(rows[0]), delimiter="\t"); w.writeheader(); w.writerows(rows)
    next(f)
    n = 0
    with gzip.open("oslo/GSE66836_beta_values.tsv.gz", "wt", compresslevel=6) as o:
        o.write("probe\t" + "\t".join(gsm) + "\n")
        for line in f:
            if line.startswith("!series_matrix_table_end"): break
            p = line.rstrip("\n").split("\t")
            vals = ["" if v in ("", "null", "NA") else f"{float(v):.3f}" for v in p[1:]]
            o.write(p[0].strip('"') + "\t" + "\t".join(vals) + "\n"); n += 1
print("probes", n, "samples", len(gsm))
from collections import Counter
print(Counter(r["tissue"] for r in rows), Counter(r["stage"] for r in rows if r["tissue"] == "tumour"))
