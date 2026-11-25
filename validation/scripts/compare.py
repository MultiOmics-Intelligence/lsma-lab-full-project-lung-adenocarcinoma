import pandas as pd, numpy as np, json
from scipy.stats import spearmanr, binomtest
B = "/tmp/lsma-showcase/"
out = {}
# 1. bulk RNA: TCGA paired vs Uppsala
t = pd.read_csv(B + "lx/export_luad_pair_run/differential_expression__tables__de_results.tsv", sep="\t")
u = pd.read_csv(B + "lx2x/lx/export_upp_run/differential_expression__tables__de_results.tsv", sep="\t")
t = t.dropna(subset=["symbol"]).drop_duplicates("symbol"); u = u.dropna(subset=["symbol"]).drop_duplicates("symbol")
m = t.merge(u, on="symbol", suffixes=("_tcga", "_upp"))
strong = m[(m.padj_tcga < 0.05) & (m.log2_fold_change_tcga.abs() >= 1)]
same = (np.sign(strong.log2_fold_change_tcga) == np.sign(strong.log2_fold_change_upp))
rep = strong[same & (strong.padj_upp < 0.05)]
rho = spearmanr(m.log2_fold_change_tcga, m.log2_fold_change_upp)[0]
out["bulk"] = {"genes_both": len(m), "strong_tcga": len(strong), "same_direction": int(same.sum()), "pct_same": round(100 * same.mean(), 1),
               "same_dir_and_sig_upp": len(rep), "pct_replicated": round(100 * len(rep) / len(strong), 1), "rho_all": round(rho, 3),
               "rho_strong": round(spearmanr(strong.log2_fold_change_tcga, strong.log2_fold_change_upp)[0], 3)}
m.to_csv("bulk_tcga_vs_uppsala.tsv", sep="\t", index=False)
# 2. methylation: TCGA paired vs Oslo
tm = pd.read_csv(B + "dmpall/luad_meth_pair_dmp_all_dmp_results_all.tsv.gz", sep="\t", usecols=["probe", "gene", "promoter", "delta_beta", "padj"])
om = pd.read_csv(B + "dmpall/oslo_dmp_all_dmp_results_all.tsv.gz", sep="\t", usecols=["probe", "delta_beta", "padj"])
mm = tm.merge(om, on="probe", suffixes=("_tcga", "_oslo"))
called = mm[(mm.padj_tcga < 0.05) & (mm.delta_beta_tcga.abs() >= 0.1)]
s2 = np.sign(called.delta_beta_tcga) == np.sign(called.delta_beta_oslo)
r2 = called[s2 & (called.padj_oslo < 0.05)]
out["methylation"] = {"cpgs_both": len(mm), "called_tcga": len(called), "pct_same": round(100 * s2.mean(), 1), "pct_replicated": round(100 * len(r2) / len(called), 1),
                      "rho_called": round(spearmanr(called.delta_beta_tcga, called.delta_beta_oslo)[0], 3)}
called.assign(replicated=s2 & (called.padj_oslo < 0.05)).to_csv("methylation_tcga_vs_oslo_called.tsv.gz", sep="\t", index=False)
# 3. promoter methylation vs expression (TCGA): genes with promoter CpGs called
prom = called[called.promoter == True].groupby("gene").delta_beta_tcga.mean()
pe = pd.DataFrame({"delta_beta": prom}).join(t.set_index("symbol").log2_fold_change, how="inner")
pe_sig = pe.join(t.set_index("symbol").padj).query("padj < 0.05")
opp = (np.sign(pe_sig.delta_beta) != np.sign(pe_sig.log2_fold_change))
out["meth_vs_expr"] = {"genes": len(pe_sig), "rho": round(spearmanr(pe_sig.delta_beta, pe_sig.log2_fold_change)[0], 3), "pct_opposite": round(100 * opp.mean(), 1),
                       "binom_p": float(binomtest(int(opp.sum()), len(opp), 0.5, alternative="greater").pvalue)}
pe_sig.to_csv("promoter_methylation_vs_expression.tsv", sep="\t")
# 4. mutations: TCGA vs Broad, OncoSG
g = pd.read_csv(B + "lx/export_luad_mut_run/landscape__tables__gene_summary.tsv", sep="\t").set_index("gene")
ind = json.load(open("/private/tmp/claude-501/-Users-anasalzaeem-Desktop-Omics-science--New-courses/0ad69610-d36c-446d-b2d5-dd90a5932a1a/scratchpad/luad/mutval/independent_cohorts.json"))
rows = []
for gene in ind["luad_broad"]["counts"]:
    r = {"gene": gene, "tcga_percent": float(g.percent_of_samples.get(gene, 0.0))}
    for st, d in ind.items(): r[f"{st}_percent"] = round(100 * d["counts"][gene] / d["n"], 1)
    rows.append(r)
mt = pd.DataFrame(rows).sort_values("tcga_percent", ascending=False)
mt.to_csv("mutation_frequencies_tcga_broad_oncosg.tsv", sep="\t", index=False)
out["mutations"] = {st: {"n": d["n"], "rho": round(spearmanr(mt.tcga_percent, mt[f"{st}_percent"])[0], 3)} for st, d in ind.items()}
json.dump(out, open("comparisons.json", "w"), indent=1)
print(json.dumps(out, indent=1))
print(mt.head(12).to_string(index=False))
