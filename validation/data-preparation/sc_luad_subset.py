# Donor-balanced random subset of the CELLxGENE LUAD atlas (dataset 01ff5cf0, 117,266 cells) to fit the lab's
# 60,000-cell import limit: 47% of each patient's cells, seed 2026. Nothing else is changed.
import anndata as ad, numpy as np
a = ad.read_h5ad("/data/scratch/luad_sc/atlas.h5ad")
x = a.X[:2000]; x = x.toarray() if hasattr(x, "toarray") else x
print("X looks like raw counts:", bool(np.allclose(x, np.round(x))), float(x.max()), "raw:", a.raw is not None)
rng = np.random.default_rng(2026)
keep = np.zeros(a.n_obs, bool)
for d, idx in a.obs.groupby("donor_id", observed=True).indices.items():
    keep[rng.choice(idx, int(round(len(idx) * 0.47)), replace=False)] = True
b = a[keep].copy()
print(b.n_obs, b.obs.groupby("donor_id", observed=True).size().to_dict())
print(b.obs["luad_histologic_subtype"].value_counts().to_dict())
print(b.obs.groupby("luad_histologic_subtype", observed=True)["donor_id"].nunique().to_dict())
b.write_h5ad("/data/scratch/luad_sc/LUAD_histologic_subtypes_47pct_per_patient.h5ad", compression="gzip")
import os; print(os.path.getsize("/data/scratch/luad_sc/LUAD_histologic_subtypes_47pct_per_patient.h5ad") / 1e6, "MB")
