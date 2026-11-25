import pandas as pd, numpy as np, json, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from lifelines import KaplanMeierFitter
NAVY, ORANGE, GREEN, CREAM, GREY = "#0F1B33", "#D9481F", "#2F7D5B", "#F6F2EA", "#8A8F9C"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": GREY})
OUT = "/Users/anasalzaeem/Desktop/Omics science /New courses/analysis-lab-showcase/lsma-lab-full-project-lung-adenocarcinoma/validation/"
cmp = json.load(open("comparisons.json"))
# ---------- Figure V1: replication of each layer
fig, ax = plt.subplots(1, 4, figsize=(18, 4.4))
m = pd.read_csv("bulk_tcga_vs_uppsala.tsv", sep="\t")
strong = (m.padj_tcga < 0.05) & (m.log2_fold_change_tcga.abs() >= 1)
ax[0].scatter(m.log2_fold_change_tcga[~strong], m.log2_fold_change_upp[~strong], s=2, c=GREY, alpha=.3, rasterized=True)
ax[0].scatter(m.log2_fold_change_tcga[strong], m.log2_fold_change_upp[strong], s=3, c=NAVY, alpha=.5, rasterized=True)
ax[0].axhline(0, c=GREY, lw=.6); ax[0].axvline(0, c=GREY, lw=.6)
b = cmp["bulk"]; ax[0].set(xlabel="log2 fold change, TCGA (paired)", ylabel="log2 fold change, Uppsala", title="A. Bulk RNA: tumour vs normal lung")
ax[0].text(.03, .97, f"{b['strong_tcga']:,} strong TCGA genes\n{b['pct_same']}% same direction\n{b['pct_replicated']}% significant in Uppsala\nρ = {b['rho_strong']}", transform=ax[0].transAxes, va="top", fontsize=8)
c = pd.read_csv("methylation_tcga_vs_oslo_called.tsv.gz", sep="\t")
ax[1].hexbin(c.delta_beta_tcga, c.delta_beta_oslo, gridsize=60, cmap="Blues", mincnt=1, bins="log")
ax[1].axhline(0, c=GREY, lw=.6); ax[1].axvline(0, c=GREY, lw=.6)
mm = cmp["methylation"]; ax[1].set(xlabel="Δβ, TCGA (paired)", ylabel="Δβ, Oslo", title="B. Methylation: tumour vs normal lung")
ax[1].text(.03, .97, f"{mm['called_tcga']:,} CpGs called in TCGA\n{mm['pct_same']}% same direction\n{mm['pct_replicated']}% significant in Oslo\nρ = {mm['rho_called']}", transform=ax[1].transAxes, va="top", fontsize=8)
mt = pd.read_csv("mutation_frequencies_tcga_broad_oncosg.tsv", sep="\t")
ax[2].plot([0, 60], [0, 60], ls="--", c=GREY, lw=.8)
ax[2].scatter(mt.tcga_percent, mt.luad_broad_percent, c=NAVY, s=22, label=f"Broad, USA (n = 183), ρ = {cmp['mutations']['luad_broad']['rho']}")
ax[2].scatter(mt.tcga_percent, mt.luad_oncosg_2020_percent, c=ORANGE, s=22, marker="s", label=f"OncoSG, Singapore (n = 302), ρ = {cmp['mutations']['luad_oncosg_2020']['rho']}")
for g in ["TP53", "KRAS", "EGFR", "STK11", "KEAP1"]:
    r = mt[mt.gene == g].iloc[0]
    for y, col in ((r.luad_broad_percent, NAVY), (r.luad_oncosg_2020_percent, ORANGE)): ax[2].annotate(g, (r.tcga_percent, y), fontsize=7, color=col, xytext=(3, 2), textcoords="offset points")
ax[2].set(xlabel="% of tumours mutated, TCGA", ylabel="% mutated, independent cohort", title="C. Mutation frequencies, 29 genes")
ax[2].legend(frameon=False, fontsize=7, loc="upper left")
pe = pd.read_csv("promoter_methylation_vs_expression.tsv", sep="\t")
ax[3].scatter(pe.delta_beta, pe.log2_fold_change, s=4, c=NAVY, alpha=.35, rasterized=True)
ax[3].axhline(0, c=GREY, lw=.6); ax[3].axvline(0, c=GREY, lw=.6)
v = cmp["meth_vs_expr"]; ax[3].set(xlabel="Promoter Δβ (mean of called CpGs), TCGA", ylabel="log2 fold change of the gene, TCGA", title="D. Promoter methylation vs expression")
ax[3].text(.97, .97, f"{v['genes']:,} genes\n{v['pct_opposite']}% move in opposite directions\nρ = {v['rho']}", transform=ax[3].transAxes, va="top", ha="right", fontsize=8)
fig.tight_layout()
for e in ("png", "pdf"): fig.savefig(OUT + f"validation-replication-across-cohorts.{e}", dpi=300 if e == "png" else None, bbox_inches="tight")
# ---------- Figure V2: what predicts death
s = pd.read_csv("solid_signature_survival.tsv", sep="\t").set_index("cohort")
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
for i, cohort in enumerate(["TCGA-LUAD", "Uppsala"]):
    d = pd.read_csv(f"solid_signature_scores_{cohort}.tsv", sep="\t")
    for grp, col, lab in (("high", ORANGE, "Solid-like score above median"), ("low", NAVY, "Solid-like score below median")):
        k = d[d.group == grp]; KaplanMeierFitter().fit(k.time / 365.25, k.event, label=f"{lab} (n = {len(k)}, {k.event.sum()} deaths)").plot_survival_function(ax=ax[i], ci_show=False, color=col, lw=2)
    r = s.loc[cohort]
    ax[i].set(ylim=(0, 1.02), xlabel="Years after diagnosis", ylabel="Share of patients alive", title=f"{'AB'[i]}. Single-cell solid signature, {cohort}")
    ax[i].text(.03, .06, f"HR per SD {r.hazard_ratio_per_sd} ({r.hr_95ci}), p = {r.cox_p:.3f}\nlog-rank p (median split) = {r.logrank_p_median_split:.3f}", transform=ax[i].transAxes, fontsize=8)
    ax[i].legend(frameon=False, fontsize=7.5, loc="lower left", bbox_to_anchor=(0, .14))
lab = ["ML survival model\nTCGA test (50)", "ML survival model\nfrozen, Uppsala (108)", "Solid signature\nTCGA (200)", "Solid signature\nUppsala (108)"]
val = [0.643, 0.493, s.loc["TCGA-LUAD", "c_index"], s.loc["Uppsala", "c_index"]]
from lifelines.utils import concordance_index
def boot(cohort):
    d = pd.read_csv(f"solid_signature_scores_{cohort}.tsv", sep="\t"); rng = np.random.default_rng(1); v = []
    for _ in range(1000):
        i = rng.integers(0, len(d), len(d))
        if d.event.values[i].sum() >= 2: v.append(concordance_index(d.time.values[i], -d.score.values[i], d.event.values[i]))
    return np.percentile(v, [2.5, 97.5])
bt, bu = boot("TCGA-LUAD"), boot("Uppsala")
json.dump({"TCGA-LUAD": bt.round(3).tolist(), "Uppsala": bu.round(3).tolist()}, open("solid_signature_cindex_intervals.json", "w"))
print("CI", bt, bu)
lo = [0.50, 0.40, bt[0], bu[0]]; hi = [0.78, 0.60, bt[1], bu[1]]
cols = [NAVY, GREY, GREEN, GREEN]; y = np.arange(4)[::-1]
for j in range(4):
    if not np.isnan(lo[j]): ax[2].plot([lo[j], hi[j]], [y[j]] * 2, c=cols[j], lw=2)
    ax[2].plot(val[j], y[j], "o", c=cols[j], ms=8)
ax[2].axvline(.5, ls="--", c=GREY, lw=1); ax[2].set_yticks(y); ax[2].set_yticklabels(lab, fontsize=8); ax[2].set_xlim(.35, .85)
ax[2].set(xlabel="Concordance index (0.5 = guessing)", title="C. Data-mined model vs biology-led signature")
fig.tight_layout()
for e in ("png", "pdf"): fig.savefig(OUT + f"validation-what-predicts-death.{e}", dpi=300 if e == "png" else None, bbox_inches="tight")
print("ok")
