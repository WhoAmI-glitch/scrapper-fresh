---
name: statistical-analysis
description: "Use when performing statistical analysis. Hypothesis tests (t-test, ANOVA, chi-square), regression, correlation, Bayesian stats, power analysis, assumption checks, APA reporting, for academic research."
---

# Statistical Analysis

## Overview

Statistical analysis is a systematic process for testing hypotheses and quantifying relationships. Conduct hypothesis tests (t-test, ANOVA, chi-square), regression, correlation, and Bayesian analyses with assumption checks and APA reporting.

## When to Use This Skill

- Conducting hypothesis tests (t-tests, ANOVA, chi-square)
- Performing regression or correlation analyses
- Running Bayesian statistical analyses
- Checking statistical assumptions and diagnostics
- Calculating effect sizes and power analyses
- Reporting results in APA format

---

## Test Selection Guide

**Comparing Two Groups:**
- Independent, normal -> Independent t-test | non-normal -> Mann-Whitney U
- Paired, normal -> Paired t-test | non-normal -> Wilcoxon signed-rank
- Binary outcome -> Chi-square or Fisher's exact

**Comparing 3+ Groups:**
- Independent, normal -> One-way ANOVA | non-normal -> Kruskal-Wallis
- Paired, normal -> Repeated measures ANOVA | non-normal -> Friedman

**Relationships:**
- Two continuous -> Pearson (normal) or Spearman (non-normal) correlation
- Continuous outcome + predictors -> Linear regression
- Binary outcome + predictors -> Logistic regression

**Bayesian Alternatives**: All tests have Bayesian versions providing direct probability statements, Bayes Factors, and null hypothesis support. See `references/bayesian_statistics.md`.

---

## Assumption Checking

**ALWAYS check assumptions before interpreting results.**

```python
from scripts.assumption_checks import comprehensive_assumption_check

results = comprehensive_assumption_check(
    data=df, value_col='score', group_col='group', alpha=0.05
)
```

This performs: outlier detection (IQR/z-score), normality (Shapiro-Wilk + Q-Q), homogeneity of variance (Levene's + box plots), and recommendations.

### When Assumptions Are Violated

**Normality violated**: Mild + n>30 -> proceed (robust) | Moderate -> non-parametric | Severe -> transform or non-parametric
**Variance violated**: t-test -> Welch's | ANOVA -> Welch's/Brown-Forsythe | Regression -> robust SEs or WLS
**Linearity violated**: Add polynomial terms, transform variables, or use non-linear models/GAM

See `references/assumptions_and_diagnostics.md` for comprehensive guidance.

---

## Running Statistical Tests

**Libraries**: scipy.stats (core tests), statsmodels (regression/diagnostics), pingouin (user-friendly with effect sizes), pymc (Bayesian), arviz (Bayesian visualization).

### T-Test with Complete Reporting

```python
import pingouin as pg

result = pg.ttest(group_a, group_b, correction='auto')
t_stat = result['T'].values[0]
df = result['dof'].values[0]
p_value = result['p-val'].values[0]
cohens_d = result['cohen-d'].values[0]
ci = result['CI95%'].values[0]

print(f"t({df:.0f}) = {t_stat:.2f}, p = {p_value:.3f}")
print(f"Cohen's d = {cohens_d:.2f}, 95% CI [{ci[0]:.2f}, {ci[1]:.2f}]")
```

### ANOVA with Post-Hoc Tests

```python
import pingouin as pg

aov = pg.anova(dv='score', between='group', data=df, detailed=True)
if aov['p-unc'].values[0] < 0.05:
    posthoc = pg.pairwise_tukey(dv='score', between='group', data=df)
    print(posthoc)
eta_squared = aov['np2'].values[0]
```

### Linear Regression with Diagnostics

```python
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

X = sm.add_constant(X_predictors)
model = sm.OLS(y, X).fit()
print(model.summary())

# Check multicollinearity
vif_data = pd.DataFrame({
    "Variable": X.columns,
    "VIF": [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
})
```

### Bayesian T-Test

```python
import pymc as pm
import arviz as az

with pm.Model() as model:
    mu1 = pm.Normal('mu_group1', mu=0, sigma=10)
    mu2 = pm.Normal('mu_group2', mu=0, sigma=10)
    sigma = pm.HalfNormal('sigma', sigma=10)
    y1 = pm.Normal('y1', mu=mu1, sigma=sigma, observed=group_a)
    y2 = pm.Normal('y2', mu=mu2, sigma=sigma, observed=group_b)
    diff = pm.Deterministic('difference', mu1 - mu2)
    trace = pm.sample(2000, tune=1000, return_inferencedata=True)

prob_greater = np.mean(trace.posterior['difference'].values > 0)
print(f"P(mu1 > mu2 | data) = {prob_greater:.3f}")
az.plot_posterior(trace, var_names=['difference'], ref_val=0)
```

---

## Effect Sizes

**Always calculate effect sizes -- they quantify magnitude while p-values only indicate existence.**

| Test | Effect Size | Small | Medium | Large |
|------|-------------|-------|--------|-------|
| T-test | Cohen's d | 0.20 | 0.50 | 0.80 |
| ANOVA | eta-squared-p | 0.01 | 0.06 | 0.14 |
| Correlation | r | 0.10 | 0.30 | 0.50 |
| Regression | R-squared | 0.02 | 0.13 | 0.26 |
| Chi-square | Cramer's V | 0.07 | 0.21 | 0.35 |

Pingouin auto-calculates most effect sizes: `pg.ttest()` returns Cohen's d, `pg.anova()` returns partial eta-squared, `pg.corr()` returns r.

---

## Power Analysis

```python
from statsmodels.stats.power import tt_ind_solve_power, FTestAnovaPower

# T-test: n needed to detect d=0.5
n = tt_ind_solve_power(effect_size=0.5, alpha=0.05, power=0.80, ratio=1.0, alternative='two-sided')

# ANOVA: n needed to detect f=0.25 with 3 groups
n_per = FTestAnovaPower().solve_power(effect_size=0.25, ngroups=3, alpha=0.05, power=0.80)

# Sensitivity: what effect can n=50/group detect?
d = tt_ind_solve_power(effect_size=None, nobs1=50, alpha=0.05, power=0.80, ratio=1.0, alternative='two-sided')
```

**Note**: Post-hoc power analysis is generally not recommended. Use sensitivity analysis instead.

---

## Reporting Results (APA Style)

### Essential Elements

1. Descriptive statistics: M, SD, n for all groups
2. Test statistics: test name, statistic, df, exact p-value
3. Effect sizes with confidence intervals
4. Assumption checks: which tests, results, actions taken
5. All planned analyses including non-significant findings

### Example Reports

**Independent T-Test**:
> Group A (n=48, M=75.2, SD=8.5) scored significantly higher than Group B (n=52, M=68.3, SD=9.2), t(98)=3.82, p<.001, d=0.77, 95% CI [0.36, 1.18]. Normality (Shapiro-Wilk: A W=0.97, p=.18; B W=0.96, p=.12) and homogeneity (Levene's F(1,98)=1.23, p=.27) satisfied.

**One-Way ANOVA**:
> Significant main effect of treatment, F(2,147)=8.45, p<.001, eta-squared-p=.10. Tukey HSD: A (M=78.2, SD=7.3) > B (M=71.5, SD=8.1, p=.002, d=0.87) and C (M=70.1, SD=7.9, p<.001, d=1.07). B vs C not significant (p=.52, d=0.18).

**Multiple Regression**:
> F(3,146)=45.2, p<.001, R-squared=.48, adj R-squared=.47. Study hours (B=1.80, beta=.35, p<.001) and prior GPA (B=8.52, beta=.28, p<.001) significant; attendance not (B=0.15, beta=.08, p=.21). All VIF<1.5.

**Bayesian**:
> Bayesian t-test with Normal(0,1) priors: M_diff=6.8, 95% credible interval [3.2, 10.4]. BF10=45.3 (very strong evidence). P(mu1>mu2|data)=99.8%. All R-hat<1.01, ESS>1000.

---

## Bayesian Statistics

**When to use**: Prior information available, direct probability statements needed, small samples, quantify evidence for null, complex models (hierarchical, missing data).

**Key advantages**: Intuitive interpretation ("95% probability parameter is in interval"), evidence for null, no p-hacking concerns, full posterior distribution.

See `references/bayesian_statistics.md` for priors, Bayes Factors, credible intervals, and model checking.

---

## Best Practices

1. Pre-register analyses when possible
2. Always check assumptions before interpreting
3. Report effect sizes with confidence intervals
4. Report all planned analyses including non-significant
5. Distinguish statistical from practical significance
6. Visualize data before and after analysis
7. Check diagnostics (residual plots, VIF)
8. Conduct sensitivity analyses for robustness
9. Share data and code for reproducibility
10. Be transparent about violations and decisions

## Common Pitfalls

1. **P-hacking**: Don't test multiple ways until significant
2. **HARKing**: Don't present exploratory as confirmatory
3. **Ignoring assumptions**: Check and report violations
4. **Significance != importance**: p<.05 does not mean meaningful
5. **Missing effect sizes**: Essential for interpretation
6. **Cherry-picking**: Report all planned analyses
7. **Misinterpreting p-values**: NOT probability hypothesis is true
8. **Multiple comparisons**: Correct for family-wise error
9. **Missing data**: Understand mechanism (MCAR, MAR, MNAR)
10. **Non-significant != no effect**: Absence of evidence != evidence of absence

---

## Resources

**References**: test_selection_guide.md, assumptions_and_diagnostics.md, effect_sizes_and_power.md, bayesian_statistics.md, reporting_standards.md

**Scripts**: assumption_checks.py (comprehensive_assumption_check, check_normality, check_homogeneity_of_variance, check_linearity, detect_outliers)
