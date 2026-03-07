import os

# Limit multi-threading to ensure reproducibility and avoid excessive CPU usage
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import pandas as pd
import numpy as np
import warnings
from scipy.interpolate import interp1d
import gc
import matplotlib.pyplot as plt

# Suppress non-critical warnings for cleaner output
warnings.simplefilter(action='ignore', category=FutureWarning)


# =====================================================
# NOTE
# The implementation here is simplified for demonstration purposes.
#
# In the full analysis, daily green space cooling capacity is estimated
# using a machine-learning model that predicts cooling effects based on
# environmental and meteorological variables.
#
# In this demo workflow, future cooling capacity is approximated by mapping
# each future day to the historical cooling capacity of the same day-of-year
# (column 'time': values 1–365).
#
# Leap year day (366) is mapped to day 365 to ensure consistent alignment
# with historical cooling records.
#
# In addition, the demo projection does not incorporate age-specific
# population changes and age-stratified exposure–response relationships
# due to data privacy restrictions. These components are included in
# the full analysis.
# =====================================================

class Config:
    """
    Configuration parameters controlling file paths
    and scenario settings for the future burden analysis.
    """

    RR_CURVE_ALL_AGE_PATH = "rr_curve.csv"
    HISTORICAL_DATA_PATH = "demo_data.csv"

    FUTURE_TEMP_PATH_TEMPLATE = "{ssp}.csv"
    FUTURE_POP_PATH_TEMPLATE = "population_{ssp}.csv"

    SSP_SCENARIOS = ['ssp126', 'ssp245', 'ssp585']


def safe_read_csv(file_path, **kwargs):
    """
    Robust CSV reader supporting multiple encodings.
    """
    try:
        return pd.read_csv(file_path, encoding='utf-8', **kwargs)
    except:
        return pd.read_csv(file_path, encoding='gbk', **kwargs)


# -----------------------------------------------------
# Load exposure–response relationship (RR curve)
# -----------------------------------------------------
def load_rr_curve_all_age(rr_file_path):

    rr_data = safe_read_csv(rr_file_path).sort_values(by='temperature')

    # Identify minimum-risk temperature (MMT)
    mmt = rr_data.loc[rr_data['RR'].idxmin(), 'temperature']

    # Interpolate RR and its confidence limits
    interp_m = interp1d(rr_data['temperature'], rr_data['RR'],
                        bounds_error=False, fill_value="extrapolate")

    interp_l = interp1d(rr_data['temperature'], rr_data['RR_low'],
                        bounds_error=False, fill_value="extrapolate")

    interp_h = interp1d(rr_data['temperature'], rr_data['RR_high'],
                        bounds_error=False, fill_value="extrapolate")

    print(f"RR curve loaded. MMT = {mmt:.2f}")

    return interp_m, interp_l, interp_h, mmt


# -----------------------------------------------------
# Load baseline epidemiological parameters and
# historical cooling capacity mapping
# -----------------------------------------------------
def load_baseline_data(historical_data_path):

    hist_df = safe_read_csv(historical_data_path)

    hist_df['NAME'] = hist_df['NAME'].astype(str)

    # Estimate baseline mental health incidence rate per person
    baseline_rate = hist_df.groupby('NAME').agg(
        t=('mental_health', 'mean'),
        p=('total_Pop', 'mean')
    ).reset_index()

    baseline_rate['baseline_rate_per_person'] = baseline_rate['t'] / baseline_rate['p']

    # Construct mapping of historical cooling capacity
    # indexed by region and day-of-year
    cooling_map = hist_df.groupby(['NAME', 'time'])['cooling_capacity'] \
                         .mean() \
                         .reset_index()

    # Extract baseline population for 'Climate-only' mode (using mean historical population)
    baseline_pop_fixed = hist_df.groupby('NAME')['total_Pop'].mean().reset_index()

    return baseline_rate[['NAME', 'baseline_rate_per_person']], cooling_map, baseline_pop_fixed


# -----------------------------------------------------
# Statistical utility functions
# -----------------------------------------------------
def reconstruct_bounds(df, prefix):
    """
    Reconstruct 95% confidence intervals from aggregated variance.
    """

    mean = df[f"{prefix}_mean"]

    se_total = np.sqrt(df[f"{prefix}_var"])

    df[f"{prefix}"] = mean
    df[f"{prefix}_low"] = mean - 1.96 * se_total
    df[f"{prefix}_high"] = mean + 1.96 * se_total


def format_ci_vectorized(df, prefix, is_per100k=False):
    """
    Format results as estimate (lower–upper) strings.
    """

    suf = "_per100k" if is_per100k else ""

    est = df[f"{prefix}{suf}"].round(2).astype(str)
    low = df[f"{prefix}_low{suf}"].round(2).astype(str)
    high = df[f"{prefix}_high{suf}"].round(2).astype(str)

    return est + " (" + low + "-" + high + ")"


# -----------------------------------------------------
# Main analysis pipeline
# -----------------------------------------------------
def run_full_analysis(mode='Climate-plus-population'):
    """
    Run the analysis pipeline.
    mode='Climate-plus-population': Future climate + Future population
    mode='Climate-only': Future climate + Fixed baseline population
    """

    cfg = Config()

    # Load exposure–response relationship
    rr_func_m, rr_func_l, rr_func_h, mmt = load_rr_curve_all_age(cfg.RR_CURVE_ALL_AGE_PATH)

    # Load baseline epidemiological parameters, cooling capacity, and fixed baseline population
    base_rate, cooling_map, baseline_pop_fixed = load_baseline_data(cfg.HISTORICAL_DATA_PATH)

    all_results = []

    for ssp in cfg.SSP_SCENARIOS:

        print(f"\nProcessing scenario: {ssp} (Mode: {mode})...")

        # -------------------------------------------------
        # Load and reshape future temperature projections
        # -------------------------------------------------
        temp_df = safe_read_csv(cfg.FUTURE_TEMP_PATH_TEMPLATE.format(ssp=ssp))

        temp_df['Date'] = pd.to_datetime(temp_df['Date'])

        future_temp = temp_df.melt(
            id_vars=['Date'],
            var_name='NAME',
            value_name='tem_mean'
        )

        future_temp['NAME'] = future_temp['NAME'].astype(str)

        future_temp['year'] = future_temp['Date'].dt.year
        future_temp['month'] = future_temp['Date'].dt.month

        # Day-of-year index
        future_temp['time'] = future_temp['Date'].dt.dayofyear
        future_temp['time'] = future_temp['time'].replace(366, 365)

        # Restrict analysis to warm season
        future_temp = future_temp[future_temp['month'].between(5, 10)]

        # -------------------------------------------------
        # Load and reshape future population projections
        # -------------------------------------------------
        if mode == 'Climate-plus-population':
            # Use dynamic future population projections
            pop_df = safe_read_csv(cfg.FUTURE_POP_PATH_TEMPLATE.format(ssp=ssp))
            future_pop = pop_df.melt(
                id_vars=['year'],
                var_name='NAME',
                value_name='total_Pop'
            )
            future_pop['NAME'] = future_pop['NAME'].astype(str)
        else:
            # Fix population at baseline level for all future years
            unique_years = future_temp['year'].unique()
            pop_list = []
            for yr in unique_years:
                temp_pop = baseline_pop_fixed.copy()
                temp_pop['year'] = yr
                pop_list.append(temp_pop)
            future_pop = pd.concat(pop_list, ignore_index=True)
            future_pop['NAME'] = future_pop['NAME'].astype(str)

        # -------------------------------------------------
        # Merge temperature, population and cooling capacity
        # -------------------------------------------------
        future_df = pd.merge(future_temp, future_pop,
                             on=['year', 'NAME'], how='left')

        future_df = pd.merge(future_df, cooling_map,
                             on=['NAME', 'time'], how='left')

        future_df = pd.merge(future_df, base_rate,
                             on='NAME', how='left')

        future_df['cooling_capacity'] = future_df['cooling_capacity'].fillna(0)

        # -------------------------------------------------
        # Vectorized epidemiological burden calculation
        # -------------------------------------------------

        # Baseline expected case count
        C = (future_df['baseline_rate_per_person'] *
             future_df['total_Pop']).fillna(0)

        # ----- Observed temperature scenario -----

        tem_obs = future_df['tem_mean']

        future_df['obs_mean'] = C * np.maximum(rr_func_m(tem_obs) - 1, 0)

        obs_low = C * np.maximum(rr_func_l(tem_obs) - 1, 0)
        obs_high = C * np.maximum(rr_func_h(tem_obs) - 1, 0)

        future_df['obs_var'] = ((obs_high - obs_low) / 3.92) ** 2

        # ----- Counterfactual temperature scenario -----

        tem_pot = tem_obs + np.abs(future_df['cooling_capacity'])

        future_df['pot_mean'] = C * np.maximum(rr_func_m(tem_pot) - 1, 0)

        pot_low = C * np.maximum(rr_func_l(tem_pot) - 1, 0)
        pot_high = C * np.maximum(rr_func_h(tem_pot) - 1, 0)

        future_df['pot_var'] = ((pot_high - pot_low) / 3.92) ** 2

        # ----- Averted burden due to cooling -----

        future_df['ave_mean'] = future_df['pot_mean'] - future_df['obs_mean']

        future_df['ave_var'] = future_df['pot_var'] + future_df['obs_var']

        # -------------------------------------------------
        # Aggregate annual burden by region
        # -------------------------------------------------
        agg_dict = {
            "obs_mean": "sum", "obs_var": "sum",
            "pot_mean": "sum", "pot_var": "sum",
            "ave_mean": "sum", "ave_var": "sum",
            "total_Pop": "mean"
        }

        agg_df = future_df.groupby(['NAME', 'year']).agg(agg_dict).reset_index()

        agg_df['ssp'] = ssp

        all_results.append(agg_df)

        gc.collect()

    # -------------------------------------------------
    # Post-processing: reconstruct CI and format outputs
    # -------------------------------------------------
    print(f"\nReconstructing CI and formatting for mode: {mode}...")

    final_df = pd.concat(all_results, ignore_index=True)

    for p in ["obs", "pot", "ave"]:
        reconstruct_bounds(final_df, p)

    for p in ["obs", "pot", "ave"]:
        for suffix in ["", "_low", "_high"]:
            final_df[f"{p}{suffix}_per100k"] = \
                (final_df[f"{p}{suffix}"] / final_df["total_Pop"]) * 100000

    for p, col_name in zip(["obs", "pot", "ave"],
                           ["observed", "potential", "averted"]):

        final_df[f"{col_name}_total"] = format_ci_vectorized(
            final_df, p, is_per100k=False
        )

        final_df[f"{col_name}_per100k"] = format_ci_vectorized(
            final_df, p, is_per100k=True
        )

    # -------------------------------------------------
    # Export final results
    # -------------------------------------------------
    keep_columns = [
        "ssp", "NAME", "year",
        "observed_total", "potential_total", "averted_total",
        "observed_per100k", "potential_per100k", "averted_per100k"
    ]

    output_name = f"future_burden_{mode}_results.csv"
    final_df[keep_columns].to_csv(output_name, index=False)

    print(f"Analysis finished. Results saved to {output_name}")


if __name__ == "__main__":

    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    print("Future burden analysis demo initializing...")

    # Run both analysis modes to separate climate and population effects
    run_full_analysis(mode='Climate-plus-population')
    run_full_analysis(mode='Climate-only')

    print("Done.")