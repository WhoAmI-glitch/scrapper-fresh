---
name: backtesting-frameworks
description: Build robust backtesting systems for trading strategies with proper handling of look-ahead bias, survivorship bias, and transaction costs. Use when developing trading algorithms, validating strategies, or building backtesting infrastructure.
---

# Backtesting Frameworks

Build robust, production-grade backtesting systems that avoid common pitfalls and produce reliable strategy performance estimates.

## When to Use This Skill

- Developing trading strategy backtests
- Building backtesting infrastructure
- Validating strategy performance
- Avoiding common backtesting biases
- Implementing walk-forward analysis

## Core Concepts

### 1. Backtesting Biases

| Bias             | Description               | Mitigation              |
| ---------------- | ------------------------- | ----------------------- |
| **Look-ahead**   | Using future information  | Point-in-time data      |
| **Survivorship** | Only testing on survivors | Use delisted securities |
| **Overfitting**  | Curve-fitting to history  | Out-of-sample testing   |
| **Selection**    | Cherry-picking strategies | Pre-registration        |
| **Transaction**  | Ignoring trading costs    | Realistic cost models   |

### 2. Proper Backtest Structure

```
Historical Data → Training Set (Development) → Validation Set (Parameter Selection) → Test Set (Final Evaluation)
```

### 3. Walk-Forward Analysis

```
Window 1: [Train------][Test]
Window 2:     [Train------][Test]
Window 3:         [Train------][Test]
```

## Pattern 1: Event-Driven Backtester

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

@dataclass
class Order:
    symbol: str
    side: OrderSide
    quantity: Decimal
    order_type: OrderType
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    timestamp: Optional[datetime] = None

@dataclass
class Fill:
    order: Order
    fill_price: Decimal
    fill_quantity: Decimal
    commission: Decimal
    slippage: Decimal
    timestamp: datetime

@dataclass
class Position:
    symbol: str
    quantity: Decimal = Decimal("0")
    avg_cost: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")

    def update(self, fill: Fill) -> None:
        if fill.order.side == OrderSide.BUY:
            new_qty = self.quantity + fill.fill_quantity
            if new_qty != 0:
                self.avg_cost = (self.quantity * self.avg_cost + fill.fill_quantity * fill.fill_price) / new_qty
            self.quantity = new_qty
        else:
            self.realized_pnl += fill.fill_quantity * (fill.fill_price - self.avg_cost)
            self.quantity -= fill.fill_quantity

@dataclass
class Portfolio:
    cash: Decimal
    positions: Dict[str, Position] = field(default_factory=dict)

    def get_position(self, symbol: str) -> Position:
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]

    def process_fill(self, fill: Fill) -> None:
        self.get_position(fill.order.symbol).update(fill)
        if fill.order.side == OrderSide.BUY:
            self.cash -= fill.fill_price * fill.fill_quantity + fill.commission
        else:
            self.cash += fill.fill_price * fill.fill_quantity - fill.commission

    def get_equity(self, prices: Dict[str, Decimal]) -> Decimal:
        equity = self.cash
        for symbol, pos in self.positions.items():
            if pos.quantity != 0 and symbol in prices:
                equity += pos.quantity * prices[symbol]
        return equity

class Strategy(ABC):
    @abstractmethod
    def on_bar(self, timestamp: datetime, data: pd.DataFrame) -> List[Order]: pass
    @abstractmethod
    def on_fill(self, fill: Fill) -> None: pass

class ExecutionModel(ABC):
    @abstractmethod
    def execute(self, order: Order, bar: pd.Series) -> Optional[Fill]: pass

class SimpleExecutionModel(ExecutionModel):
    def __init__(self, slippage_bps: float = 10, commission_per_share: float = 0.01):
        self.slippage_bps = slippage_bps
        self.commission_per_share = commission_per_share

    def execute(self, order: Order, bar: pd.Series) -> Optional[Fill]:
        if order.order_type == OrderType.MARKET:
            base_price = Decimal(str(bar["open"]))
            slippage_mult = 1 + (self.slippage_bps / 10000)
            fill_price = base_price * Decimal(str(slippage_mult)) if order.side == OrderSide.BUY else base_price / Decimal(str(slippage_mult))
            return Fill(order=order, fill_price=fill_price, fill_quantity=order.quantity,
                        commission=order.quantity * Decimal(str(self.commission_per_share)),
                        slippage=abs(fill_price - base_price) * order.quantity, timestamp=bar.name)
        return None

class Backtester:
    def __init__(self, strategy: Strategy, execution_model: ExecutionModel, initial_capital: Decimal = Decimal("100000")):
        self.strategy = strategy
        self.execution_model = execution_model
        self.portfolio = Portfolio(cash=initial_capital)
        self.equity_curve: List[tuple] = []
        self.trades: List[Fill] = []

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        pending_orders: List[Order] = []
        for timestamp, bar in data.iterrows():
            for order in pending_orders:
                fill = self.execution_model.execute(order, bar)
                if fill:
                    self.portfolio.process_fill(fill)
                    self.strategy.on_fill(fill)
                    self.trades.append(fill)
            pending_orders.clear()
            prices = {data.index.name or "default": Decimal(str(bar["close"]))}
            self.equity_curve.append((timestamp, float(self.portfolio.get_equity(prices))))
            pending_orders.extend(self.strategy.on_bar(timestamp, data.loc[:timestamp]))
        equity_df = pd.DataFrame(self.equity_curve, columns=["timestamp", "equity"])
        equity_df.set_index("timestamp", inplace=True)
        equity_df["returns"] = equity_df["equity"].pct_change()
        return equity_df
```

## Pattern 2: Vectorized Backtester (Fast)

```python
class VectorizedBacktester:
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run(self, prices: pd.DataFrame, signal_func) -> Dict:
        signals = signal_func(prices).shift(1).fillna(0)
        returns = prices["close"].pct_change()
        trading_costs = signals.diff().abs() * (self.commission + self.slippage)
        strategy_returns = signals * returns - trading_costs
        equity = (1 + strategy_returns).cumprod() * self.initial_capital
        return {"equity": equity, "returns": strategy_returns, "signals": signals,
                "metrics": self._calculate_metrics(strategy_returns, equity)}

    def _calculate_metrics(self, returns, equity) -> Dict:
        total_return = (equity.iloc[-1] / self.initial_capital) - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        annual_vol = returns.std() * np.sqrt(252)
        rolling_max = equity.cummax()
        max_drawdown = ((equity - rolling_max) / rolling_max).min()
        winning = (returns > 0).sum()
        total = (returns != 0).sum()
        return {"total_return": total_return, "annual_return": annual_return,
                "annual_volatility": annual_vol,
                "sharpe_ratio": annual_return / annual_vol if annual_vol > 0 else 0,
                "max_drawdown": max_drawdown,
                "win_rate": winning / total if total > 0 else 0,
                "num_trades": int(total)}
```

## Performance Metrics

```python
def calculate_metrics(returns: pd.Series, rf_rate: float = 0.02) -> Dict:
    ann = 252
    total_return = (1 + returns).prod() - 1
    annual_return = (1 + total_return) ** (ann / len(returns)) - 1
    annual_vol = returns.std() * np.sqrt(ann)
    sharpe = (annual_return - rf_rate) / annual_vol if annual_vol > 0 else 0
    downside = returns[returns < 0]
    downside_vol = downside.std() * np.sqrt(ann)
    sortino = (annual_return - rf_rate) / downside_vol if downside_vol > 0 else 0
    equity = (1 + returns).cumprod()
    max_dd = ((equity - equity.cummax()) / equity.cummax()).min()
    calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    return {"total_return": total_return, "annual_return": annual_return,
            "annual_volatility": annual_vol, "sharpe_ratio": sharpe,
            "sortino_ratio": sortino, "calmar_ratio": calmar,
            "max_drawdown": max_dd,
            "win_rate": len(wins) / len(returns[returns != 0]) if len(returns[returns != 0]) > 0 else 0,
            "profit_factor": wins.sum() / abs(losses.sum()) if losses.sum() != 0 else np.inf}
```

## Best Practices

### Do's

- **Use point-in-time data** - Avoid look-ahead bias
- **Include transaction costs** - Realistic estimates
- **Test out-of-sample** - Always reserve data
- **Use walk-forward** - Not just train/test
- **Monte Carlo analysis** - Understand uncertainty

### Don'ts

- **Don't overfit** - Limit parameters
- **Don't ignore survivorship** - Include delisted
- **Don't use adjusted data carelessly** - Understand adjustments
- **Don't optimize on full history** - Reserve test set
- **Don't ignore capacity** - Market impact matters
