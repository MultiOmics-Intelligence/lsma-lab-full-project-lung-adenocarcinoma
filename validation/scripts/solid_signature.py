"""Pre-specified cross-layer test. Signature from single-cell (tumour epithelial cells, solid vs acinar/papillary,
pseudobulk DESeq2 in the lab): the 50 genes most significantly higher and the 50 most significantly lower in solid
tumours (padj < 0.05, |log2FC| >= 1). Score per bulk tumour = mean z(log2 CPM+1) of the up genes minus that of the down
genes, z computed within each cohort. Tested against overall survival in TCGA-LUAD (200) and Uppsala (108 LUAD)."""
import pandas as pd, numpy as np, json
from lifelines import CoxPHFitter
from lifelines.statistics import logrank_test
from lifelines.utils import concordance_index
B = "/tmp/lsma-showcase/"
de = pd.read_csv(B + "lx2x/lx/export_luad_sc_run/differential_expression__tables__pseudobulk_de.tsv", sep="\t")
ep = de[(de.cell_type == "epithelial cell of lung") & (de.padj < 0.05) & (de.log2_fold_change.abs() >= 1)].sort_values("padj")
up = ep[ep.log2_fold_change > 0].gene.head(50).tolist(); down = ep[ep.log2_fold_change < 0].gene.head(50).tolist()
def logcpm(path, name_col):
    t = pd.read_csv(path, sep="\t")
    names = t[name_col].astype(str); x = t.drop(columns=[c for c in t.columns if not pd.api.types.is_numeric_dtype(t[c])])
    x = x.loc[:, [c for c in x.columns if c not in ("gene_id",)]]
    cpm = np.log2(x / x.sum(0) * 1e6 + 1); cpm.index = names
    return cpm.groupby(level=0).mean()
def score(cpm):
    z = cpm.sub(cpm.mean(1), axis=0).div(cpm.std(1).replace(0, np.nan), axis=0)
    u = [g for g in up if g in z.index]; d = [g for g in down if g in z.index]
    return z.loc[u].mean() - z.loc[d].mean(), len(u), len(d)
res = {"genes_up": up, "genes_down": down}
cohorts = {
  "TCGA-LUAD": (B + "tc/TCGA-LUAD_rna_counts.tsv.gz", "gene_name", B + "tc/TCGA-LUAD_rna_sample_metadata.tsv"),
  "Uppsala": ("/private/tmp/claude-501/-Users-anasalzaeem-Desktop-Omics-science--New-courses/0ad69610-d36c-446d-b2d5-dd90a5932a1a/scratchpad/luad/uppsala/GSE81089_LUAD_counts.tsv.gz", "gene_name",
              "/private/tmp/claude-501/-Users-anasalzaeem-Desktop-Omics-science--New-courses/0ad69610-d36c-446d-b2d5-dd90a5932a1a/scratchpad/luad/uppsala/GSE81089_LUAD_sample_sheet.tsv")}
rows = []
for name, (cp, nc, sp) in cohorts.items():
    cpm = logcpm(cp, nc); sh = pd.read_csv(sp, sep="\t").set_index("sample_id")
    if "tissue" in sh: sh = sh[sh.tissue == "tumour"]
    cpm = cpm.loc[:, [c for c in cpm.columns if c in sh.index]]
    s, nu, nd = score(cpm)
    df = pd.DataFrame({"score": (s - s.mean()) / s.std(), "time": sh.loc[s.index, "survival_days"].astype(float), "event": (sh.loc[s.index, "vital_status"] == "Dead").astype(int)}).dropna()
    df = df[df.time >= 0]
    cph = CoxPHFitter().fit(df, "time", "event")
    hr = float(np.exp(cph.params_["score"])); lo, hi = np.exp(cph.confidence_intervals_.loc["score"]).tolist(); p = float(cph.summary.loc["score", "p"])
    high = df.score > df.score.median()
    lr = logrank_test(df.time[high], df.time[~high], df.event[high], df.event[~high]).p_value
    c = concordance_index(df.time, -df.score, df.event)
    stage = sh.loc[df.index, "stage"] if "stage" in sh else None
    rows.append({"cohort": name, "patients": len(df), "deaths": int(df.event.sum()), "genes_up_found": nu, "genes_down_found": nd,
                 "hazard_ratio_per_sd": round(hr, 3), "hr_95ci": f"{lo:.2f} to {hi:.2f}", "cox_p": p, "c_index": round(c, 3), "logrank_p_median_split": float(lr)})
    df.assign(group=np.where(high, "high", "low")).to_csv(f"solid_signature_scores_{name}.tsv", sep="\t")
    # adjusted for stage
    if stage is not None:
        st = stage.str.extract(r"Stage (I{1,3}V?|IV)")[0]
        adv = st.isin(["III", "IV"]).astype(int); ok = st.notna()
        d2 = df[ok].assign(advanced_stage=adv[ok])
        c2 = CoxPHFitter().fit(d2, "time", "event")
        rows[-1].update({"hr_adjusted_for_stage": round(float(np.exp(c2.params_["score"])), 3), "p_adjusted_for_stage": float(c2.summary.loc["score", "p"])})
out = pd.DataFrame(rows); out.to_csv("solid_signature_survival.tsv", sep="\t", index=False)
print(out.to_string(index=False)); print("UP", up[:15]); print("DOWN", down[:15])
json.dump(res, open("solid_signature_genes.json", "w"), indent=1)
