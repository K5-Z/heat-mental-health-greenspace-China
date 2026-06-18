############################################################
# Distributed Lag Non-linear Model (DLNM) demonstration code
# This script reproduces the core statistical analysis used
# in the study using a simplified demo dataset.
############################################################

# Load required packages
library(data.table)
library(dlnm)
library(gnm)
library(splines)

############################################################
# 1. Read demo dataset
############################################################

data <- fread("demo_data.csv")

############################################################
# 2. Variable preprocessing
############################################################

# Convert categorical variables
data$NAME <- as.factor(data$NAME)
data$dow  <- as.factor(data$dow)

# Create mental health search rate
data$mental_healthP <- with(data, mental_health / total_Pop * 100000)

# Remove unrealistic temperature values
data$tem_mean[data$tem_mean < -40 | data$tem_mean > 50] <- NA

############################################################
# 3. Define cross-basis for temperature
############################################################

# DLNM with 14-day lag
cb_tem <- crossbasis(
  data$tem_mean,
  lag = 14,
  argvar = list(
    fun = "ns",
    knots = equalknots(data$tem_mean, nk = 4)
  ),
  arglag = list(
    fun = "ns",
    knots = logknots(14, 3)
  )
)

############################################################
# 4. Define fixed effects (county-level)
############################################################

data$stratum <- factor(data$NAME)

############################################################
# 5. Fit DLNM model
############################################################

# Natural spline for long-term and seasonal trends
# In the full analysis, 5 degrees of freedom per year were used.
# Since the demo dataset contains one year of data, df = 5 is used here.

model <- gnm(
  mental_healthP ~ cb_tem +
    ns(time, 5) +
    dow +
    rh +
    precipitation +
    wind_speed,
  eliminate = stratum,
  family = quasipoisson,
  data = data
)

############################################################
# 6. Predict temperature–mental health relationship
############################################################

pred <- crosspred(
  cb_tem,
  model,
  cen = quantile(data$tem_mean, 0.5, na.rm = TRUE)
)

############################################################
# 7. Identify minimum mental-health temperature (MMT)
############################################################

mmt <- pred$predvar[which.min(pred$allRRfit)]
print(paste("Minimum mental-health temperature:", mmt))

############################################################
# 8. Export relative risk estimates
############################################################

results <- data.frame(
  temperature = pred$predvar,
  RR = pred$allRRfit,
  RR_low = pred$allRRlow,
  RR_high = pred$allRRhigh
)

write.csv(results, "demo_rr_curve.csv", row.names = FALSE)

############################################################
# End of script
############################################################