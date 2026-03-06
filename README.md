# Green space-facilitated cooling mitigates heat-related mental ill-health: National, high spatiotemporal-resolution evidence from China
This repository provides **demo code and example datasets** used to reproduce the analytical workflow in the study:

**Green space-facilitated cooling mitigates heat-related mental ill-health: National, high spatiotemporal-resolution evidence from China**

The code demonstrates the core analytical pipeline used in the study, including:

- Estimation of temperature–mental health exposure–response relationships using **Distributed Lag Non-linear Models (DLNM)**  
- Calculation of **historical heat-related mental health burden**  
- Projection of **future heat-related mental health burden under climate change scenarios**

Because the original mental health search query data are subject to privacy and proprietary restrictions, the full dataset cannot be publicly released. To allow users to reproduce the computational workflow, this repository provides a demo dataset consisting of data from two counties randomly selected from the 2022 records. In the demonstration workflow for future projections, several simplifying assumptions are adopted: the population age structure is assumed to remain constant, and relative risk (RR) estimates are not stratified by age group. These simplifications are used solely to illustrate the analytical procedure. Researchers may contact the corresponding author to request access to the full dataset for reasonable research purposes.

---

# Repository contents

The repository contains the following scripts and demo datasets.

## Code

- `demo_statistical_modelling.R`  
  Estimates the exposure–response relationship between temperature and mental health distress using DLNM.

- `demo_burden.py`  
  Calculates historical heat-related mental health burden and the potential reduction attributable to green space cooling.

- `demo_future_burden.py`  
  Projects future heat-related mental health burden under two scenarios: climate change only, and combined climate and population change.

---

## Data

- `demo_data.csv`  
  Example dataset used for model estimation and historical burden calculations.

- `rr_curve.csv`  
  Temperature–risk curve estimated from the DLNM model.

- `ssp126.csv`, `ssp245.csv`, `ssp585.csv`  
  Example climate projection datasets under different SSP scenarios.

- `population_ssp126.csv`, `population_ssp245.csv`, `population_ssp585.csv`  
  Example population projection datasets corresponding to the climate scenarios.

---

# System requirements

The code was tested using:

- Python 3.9.15
- R 4.5.0

Required Python libraries:

- pandas
- numpy
- scipy
- matplotlib

Required R packages:

- data.table
- dlnm
- gnm
- splines
---

# Installation

No special installation is required beyond the Python and R dependencies listed above. Users should ensure that the required packages are installed in their environment before running the scripts.

---

# Usage

The analytical workflow can be reproduced using the following steps.

## Step 1. Estimate temperature–mental health exposure–response relationship

Run the R script:

`demo_statistical_modelling.R`

This script fits a **Distributed Lag Non-linear Model (DLNM)** to estimate the temperature–mental health exposure–response relationship and identifies the **minimum mental-health temperature (MMT)**.

The script outputs the estimated temperature–risk curve:

`demo_rr_curve.csv`

## Step 2. Estimate historical heat-related mental health burden

Run the Python script:

`demo_burden.py`

This script quantifies the **heat-attributable mental health burden** during the warm season based on the estimated temperature–mental health exposure–response relationship.

Using the minimum mental-health temperature (MMT) as the reference level, the script calculates the daily attributable fraction and aggregates it to obtain the **annual mean heat-related mental health burden**.

To assess the mitigating effects of green space, a counterfactual **no-green-space scenario** is constructed by removing the cooling contribution of green space from the observed temperature series. The difference between the counterfactual burden and the observed burden represents the **mental health burden mitigated by green space cooling**
## Step 3. Project future heat-related mental health burden

Run the Python script:

`demo_future_burden.py`

This script projects future **heat-related mental health burden** under different climate and demographic scenarios using the previously estimated exposure–response relationship.

Future temperature projections are derived from climate datasets under three Shared Socioeconomic Pathways (SSPs):

- SSP1–2.6  
- SSP2–4.5  
- SSP5–8.5  

Two projection scenarios are implemented:

- **Climate-only (CO) scenario** – future temperature changes are considered while population size remains fixed at baseline levels.
- **Climate-plus-population (CP) scenario** – both climate change and population dynamics are incorporated.

Under each scenario, the exposure–response relationship is assumed to remain constant, and projected temperature series are applied to estimate future heat-attributable mental health burden. The resulting estimates illustrate potential changes in population-level mental health risks under different climate and demographic trajectories.
# Expected outputs

Running the scripts will generate several output files, including:

- Temperature–risk curve estimated from the DLNM model
- Historical heat-related mental health burden estimates
- Projected future heat-related mental health burden under different scenarios

These outputs are generated using the demo dataset and serve only to illustrate the analytical workflow.

---

# Reproducibility

The code provided in this repository reproduces the **analytical workflow** used in the study but does not include the full original dataset due to privacy and proprietary restrictions.

The demo dataset is intended solely to demonstrate the computational procedures.

---

# Contact

For questions regarding the code or data access requests, please contact the corresponding author.

---

# Citation

If you use this code in your research, please cite:

Green space-facilitated cooling mitigates heat-related mental ill-health: National, high spatiotemporal-resolution evidence from China
