---
name: risk-metrics-calculation
description: Calculate portfolio risk metrics including VaR, CVaR, Sharpe, Sortino, and drawdown analysis. Use when measuring portfolio risk, implementing risk limits, or building risk monitoring systems.
---

# Risk Metrics Calculation

Comprehensive risk measurement toolkit for portfolio management.

## When to Use This Skill

- Measuring portfolio risk
- Implementing risk limits
- Building risk dashboards
- Calculating risk-adjusted returns
- Setting position sizes

## Core Concepts

| Category          | Metrics         | Use Case             |
| ----------------- | --------------- | -------------------- |
| **Volatility**    | Std Dev, Beta   | General risk         |
| **Tail Risk**     | VaR, CVaR       | Extreme losses       |
| **Drawdown**      | Max DD, Calmar  | Capital preservation |
| **Risk-Adjusted** | Sharpe, Sortino | Performance          |

## Pattern 1: Core Risk Metrics

```python
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Optional

class RiskMetrics:
    def __init__(self, returns: pd.Series, rf_rate: float = 0.02):
        self.returns = returns
        self.rf_rate = rf_rate
        self.ann_factor = 252

    def volatility(self, annualized: bool = True) -> float:
        vol = self.returns.std()
        return vol * np.sqrt(self.ann_factor) if annualized else vol

    def downside_deviation(self, threshold: float = 0, annualized: bool = True) -> float:
        downside = self.returns[self.returns < threshold]
        if len(downside) == 0: return 0.0
        dd = downside.std()
        return dd * np.sqrt(self.ann_factor) if annualized else dd

    def beta(self, market_returns: pd.Series) -> float:
        aligned = pd.concat([self.returns, market_returns], axis=1).dropna()
        if len(aligned) < 2: return np.nan
        cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
        return cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0

    def var_historical(self, confidence: float = 0.95) -> float:
        return -np.percentile(self.returns, (1 - confidence) * 100)

    def var_parametric(self, confidence: float = 0.95) -> float:
        z = stats.norm.ppf(confidence)
        return self.returns.mean() - z * self.returns.std()

    def cvar(self, confidence: float = 0.95) -> float:
        var = self.var_historical(confidence)
        return -self.returns[self.returns <= -var].mean()

    def drawdowns(self) -> pd.Series:
        cumulative = (1 + self.returns).cumprod()
        return (cumulative - cumulative.cummax()) / cumulative.cummax()

    def max_drawdown(self) -> float:
        return self.drawdowns().min()

    def sharpe_ratio(self) -> float:
        excess = self.returns.mean() * self.ann_factor - self.rf_rate
        vol = self.volatility()
        return excess / vol if vol > 0 else 0

    def sortino_ratio(self) -> float:
        excess = self.returns.mean() * self.ann_factor - self.rf_rate
        dd = self.downside_deviation()
        return excess / dd if dd > 0 else 0

    def calmar_ratio(self) -> float:
        annual_ret = (1 + self.returns).prod() ** (self.ann_factor / len(self.returns)) - 1
        max_dd = abs(self.max_drawdown())
        return annual_ret / max_dd if max_dd > 0 else 0

    def omega_ratio(self, threshold: float = 0) -> float:
        above = (self.returns[self.returns > threshold] - threshold).sum()
        below = (threshold - self.returns[self.returns <= threshold]).sum()
        return above / below if below != 0 else np.inf

    def summary(self) -> Dict[str, float]:
        return {
            "total_return": (1 + self.returns).prod() - 1,
            "annual_return": (1 + self.returns).prod() ** (self.ann_factor / len(self.returns)) - 1,
            "annual_volatility": self.volatility(),
            "var_95": self.var_historical(0.95),
            "cvar_95": self.cvar(0.95),
            "max_drawdown": self.max_drawdown(),
            "sharpe_ratio": self.sharpe_ratio(),
            "sortino_ratio": self.sortino_ratio(),
            "calmar_ratio": self.calmar_ratio(),
            "skewness": stats.skew(self.returns),
            "kurtosis": stats.kurtosis(self.returns),
        }
```

## Pattern 2: Portfolio Risk

```python
class PortfolioRisk:
    def __init__(self, returns: pd.DataFrame, weights: Optional[pd.Series] = None):
        self.returns = returns
        self.weights = weights if weights is not None else pd.Series(1/len(returns.columns), index=returns.columns)
        self.ann_factor = 252

    def portfolio_volatility(self) -> float:
        cov = self.returns.cov() * self.ann_factor
        return np.sqrt(self.weights @ cov @ self.weights)

    def marginal_risk_contribution(self) -> pd.Series:
        cov = self.returns.cov() * self.ann_factor
        return (cov @ self.weights) / self.portfolio_volatility()

    def component_risk(self) -> pd.Series:
        return self.weights * self.marginal_risk_contribution()

    def diversification_ratio(self) -> float:
        asset_vols = self.returns.std() * np.sqrt(self.ann_factor)
        return (self.weights * asset_vols).sum() / self.portfolio_volatility()

    def conditional_correlation(self, threshold_pct: float = 10) -> pd.DataFrame:
        port_ret = self.returns @ self.weights
        return self.returns[port_ret <= np.percentile(port_ret, threshold_pct)].corr()
```

## Pattern 3: Rolling Risk Metrics

```python
class RollingRiskMetrics:
    def __init__(self, returns: pd.Series, window: int = 63):
        self.returns = returns
        self.window = window

    def rolling_volatility(self, annualized: bool = True) -> pd.Series:
        vol = self.returns.rolling(self.window).std()
        return vol * np.sqrt(252) if annualized else vol

    def rolling_sharpe(self, rf_rate: float = 0.02) -> pd.Series:
        return (self.returns.rolling(self.window).mean() * 252 - rf_rate) / self.rolling_volatility()

    def rolling_var(self, confidence: float = 0.95) -> pd.Series:
        return self.returns.rolling(self.window).apply(
            lambda x: -np.percentile(x, (1 - confidence) * 100), raw=True)

    def volatility_regime(self, low: float = 0.10, high: float = 0.20) -> pd.Series:
        vol = self.rolling_volatility()
        return vol.apply(lambda v: "low" if v < low else ("high" if v > high else "normal"))
```

## Pattern 4: Stress Testing

```python
class StressTester:
    SCENARIOS = {
        "2008_crisis": ("2008-09-01", "2009-03-31"),
        "2020_covid": ("2020-02-19", "2020-03-23"),
        "2022_rates": ("2022-01-01", "2022-10-31"),
    }

    def __init__(self, returns: pd.Series, weights: pd.Series = None):
        self.returns = returns
        self.weights = weights

    def historical_stress(self, scenario: str, data: pd.DataFrame) -> Dict:
        start, end = self.SCENARIOS[scenario]
        crisis = data.loc[start:end]
        port = (crisis @ self.weights) if self.weights is not None else crisis
        cumulative = (1 + port).cumprod()
        return {"total_return": (1 + port).prod() - 1,
                "max_drawdown": ((cumulative - cumulative.cummax()) / cumulative.cummax()).min(),
                "worst_day": port.min(), "volatility": port.std() * np.sqrt(252)}

    def monte_carlo_stress(self, n_sims: int = 10000, horizon: int = 21, vol_mult: float = 2.0) -> Dict:
        sims = np.random.normal(self.returns.mean(), self.returns.std() * vol_mult, (n_sims, horizon))
        total = (1 + sims).prod(axis=1) - 1
        return {"expected_loss": -total.mean(), "var_95": -np.percentile(total, 5),
                "var_99": -np.percentile(total, 1), "worst_case": -total.min()}
```

## Best Practices

- **Use multiple metrics** - No single metric captures all risk
- **Consider tail risk** - VaR alone underestimates; use CVaR
- **Rolling analysis** - Risk changes over time
- **Stress test** - Historical and hypothetical scenarios
- **Don't assume normality** - Returns are fat-tailed
- **Don't ignore correlation** - It increases in stress periods
