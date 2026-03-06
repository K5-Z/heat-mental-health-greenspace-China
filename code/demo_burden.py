import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

############################################################
# 1. Load data
############################################################

mh_data = pd.read_csv("demo_data.csv")
rr_data = pd.read_csv("rr_curve.csv").sort_values("temperature")

############################################################
# 2. Prepare ONE exposure–response relationship (Vectorized)
############################################################

rr_interp_multi = interp1d(
    rr_data["temperature"],
    rr_data[["RR", "RR_low", "RR_high"]],
    kind="linear",
    bounds_error=False,
    fill_value="extrapolate",
    axis=0
)


############################################################
# 3. Calculate attributable burden with Variance (Numpy Broadcasting)
############################################################

def calculate_burden_with_variance(df):
    rr_arr = rr_interp_multi(df["tem_mean"])
    rr_cf_arr = rr_interp_multi(df["tem_mean"] - df["cooling_capacity"])

    af_arr = (rr_arr - 1) / rr_arr
    af_cf_arr = (rr_cf_arr - 1) / rr_cf_arr

    mh_arr = df["mental_health"].values[:, np.newaxis]

    obs_arr = af_arr * mh_arr
    pot_arr = af_cf_arr * mh_arr

    obs_mean = obs_arr[:, 0]
    obs_se = (obs_arr[:, 2] - obs_arr[:, 1]) / 3.92
    obs_var = obs_se ** 2

    pot_mean = pot_arr[:, 0]
    pot_se = (pot_arr[:, 2] - pot_arr[:, 1]) / 3.92
    pot_var = pot_se ** 2

    ave_mean = pot_mean - obs_mean
    ave_var = pot_var + obs_var

    df["obs_mean"], df["obs_var"] = obs_mean, obs_var
    df["pot_mean"], df["pot_var"] = pot_mean, pot_var
    df["ave_mean"], df["ave_var"] = ave_mean, ave_var

    return df


############################################################
# 4. Run burden calculation & Aggregate
############################################################

results = calculate_burden_with_variance(mh_data)

agg_dict = {
    "obs_mean": "sum", "obs_var": "sum",
    "pot_mean": "sum", "pot_var": "sum",
    "ave_mean": "sum", "ave_var": "sum",
    "total_Pop": "mean"
}

summary = results.groupby(["NAME", "year", "month"]).agg(agg_dict).reset_index()


############################################################
# 5. Reconstruct 95% Confidence Intervals & Per 100k
############################################################

def reconstruct_bounds(df, prefix):
    mean = df[f"{prefix}_mean"]
    se_total = np.sqrt(df[f"{prefix}_var"])

    df[f"{prefix}"] = mean
    df[f"{prefix}_low"] = mean - 1.96 * se_total
    df[f"{prefix}_high"] = mean + 1.96 * se_total


for p in ["obs", "pot", "ave"]:
    reconstruct_bounds(summary, p)

for p in ["obs", "pot", "ave"]:
    for suffix in ["", "_low", "_high"]:
        summary[f"{p}{suffix}_per100k"] = (summary[f"{p}{suffix}"] / summary["total_Pop"]) * 100000


############################################################
# 6. Format output (Vectorized String Ops)
############################################################

def format_ci_vectorized(df, prefix, is_per100k=False):
    suf = "_per100k" if is_per100k else ""
    est = df[f"{prefix}{suf}"].round(2).astype(str)
    low = df[f"{prefix}_low{suf}"].round(2).astype(str)
    high = df[f"{prefix}_high{suf}"].round(2).astype(str)
    return est + " (" + low + "-" + high + ")"


for p, col_name in zip(["obs", "pot", "ave"], ["observed", "potential", "averted"]):
    summary[f"{col_name}_total"] = format_ci_vectorized(summary, p, is_per100k=False)
    summary[f"{col_name}_per100k"] = format_ci_vectorized(summary, p, is_per100k=True)

############################################################
# 7. Final output
############################################################

keep_columns = [
    "NAME", "year", "month",
    "observed_total", "potential_total", "averted_total",
    "observed_per100k", "potential_per100k", "averted_per100k"
]

summary[keep_columns].to_csv("burden_demo_results.csv", index=False)