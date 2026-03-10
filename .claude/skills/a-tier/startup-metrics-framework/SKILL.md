---
name: startup-metrics-framework
description: Use when the user asks about "key startup metrics", "SaaS metrics", "CAC and LTV", "unit economics", "burn multiple", "rule of 40", "marketplace metrics", or requests guidance on tracking and optimizing business performance metrics.
version: 1.0.0
---

# Startup Metrics Framework

Track, calculate, and optimize key performance metrics for different startup business models from seed through Series A.

## Universal Startup Metrics

### Revenue Metrics

**MRR** = Sum of (Active Subscriptions x Monthly Price)
**ARR** = MRR x 12
**MoM Growth** = (This Month MRR - Last Month MRR) / Last Month MRR
**YoY Growth** = (This Year ARR - Last Year ARR) / Last Year ARR

**Benchmarks**: Seed 15-20% MoM | Series A 10-15% MoM, 3-5x YoY | Series B+ 100%+ YoY

### Unit Economics

**CAC** = Total S&M Spend / New Customers Acquired (include salaries, marketing, tools, overhead)
**LTV** = ARPU x Gross Margin% x (1 / Churn Rate)
**LTV:CAC Ratio**: >3.0 Healthy | 1.0-3.0 Needs improvement | <1.0 Unsustainable
**CAC Payback** = CAC / (ARPU x Gross Margin%): <12mo Excellent | 12-18mo Good | >24mo Concerning

### Cash Efficiency

**Monthly Burn** = Monthly Revenue - Monthly Expenses (negative = losing money)
**Runway** = Cash Balance / Monthly Burn Rate (target: 12-18 months)
**Burn Multiple** = Net Burn / Net New ARR: <1.0 Exceptional | 1.0-1.5 Good | 1.5-2.0 Acceptable | >2.0 Inefficient

## SaaS Metrics

### Revenue Composition

**Net New MRR** = New MRR + Expansion MRR - Contraction MRR - Churned MRR

### Retention

**Logo Retention** = (Customers End - New Customers) / Customers Start
**NDR (Net Dollar Retention)** = (ARR Start + Expansion - Contraction - Churn) / ARR Start
NDR Benchmarks: >120% Best-in-class | 100-120% Good | <100% Needs work
**Gross Retention** = (ARR Start - Churn - Contraction) / ARR Start: >90% Excellent | 85-90% Good | <85% Concerning

### SaaS-Specific

**Magic Number** = Net New ARR (quarter) / S&M Spend (prior quarter): >0.75 Scale-ready | 0.5-0.75 Moderate | <0.5 Don't scale
**Rule of 40** = Revenue Growth Rate% + Profit Margin%: >40% Excellent | 20-40% Acceptable | <20% Needs improvement
**Quick Ratio** = (New MRR + Expansion MRR) / (Churned MRR + Contraction MRR): >4.0 Healthy | 2.0-4.0 Moderate | <2.0 Churn problem

## Marketplace Metrics

**GMV** = Sum of all transaction values (target 20%+ MoM early-stage)
**Take Rate** = Net Revenue / GMV (Payment processors 2-3% | E-commerce 10-20% | Services 15-25% | B2B 5-15%)

**Liquidity Indicators**: Time to Transaction, Fill Rate (>80% = strong), Repeat Rate (>60% = strong retention)
**Balance**: Track supply/demand ratio. Too much supply = low fill rates; too much demand = long wait times.

## Consumer/Mobile Metrics

**DAU/MAU Ratio**: >50% Exceptional (daily habit) | 20-50% Good | <20% Weak engagement

**Retention Curves** (Day 30): >40% Excellent | 25-40% Good | <25% Weak. Flattening curve = good (habitual users).

**K-Factor** = Invites per User x Invite Conversion Rate: >1.0 Viral | 0.5-1.0 Strong referrals | <0.5 Weak virality

## B2B Metrics

**Win Rate** = Deals Won / Total Opportunities (target 20-30% new, 30-40% mature)
**Sales Cycle**: SMB 30-60 days | Mid-market 60-120 days | Enterprise 120-270 days
**ACV** = Total Contract Value / Contract Length (years)
**Pipeline Coverage** = Total Pipeline Value / Quota (target 3-5x)

## Metrics by Stage

### Pre-Seed (Product-Market Fit)
**Focus**: Active users growth, retention (Day 7/30), core engagement, qualitative feedback (NPS). Don't worry about revenue, CAC, or unit economics yet.

### Seed ($500K-$2M ARR)
**Focus**: MRR growth (15-20% MoM), CAC/LTV baseline, gross retention (>85%), product engagement. Start tracking sales efficiency and burn/runway.

### Series A ($2M-$10M ARR)
**Focus**: ARR growth (3-5x YoY), LTV:CAC >3, payback <18mo, NDR >100%, burn multiple <2.0, magic number >0.5. Mature tracking: Rule of 40, sales efficiency, pipeline coverage.

## Best Practices

**Infrastructure**: Single source of truth, real-time/daily updates, automated calculations, historical tracking. Tools: Mixpanel/Amplitude (product), ChartMogul/Baremetrics (SaaS), Looker/Tableau (BI).

**Cadence**: Daily (MRR, active users, conversions) | Weekly (growth rates, retention, pipeline) | Monthly (full suite, board/investor reporting) | Quarterly (trends, benchmarking, strategy).

**Common Mistakes**: (1) Vanity metrics -- focus on actionable metrics tied to value, not total users/pageviews/downloads. (2) Too many metrics -- track 5-7 core intensely, not 50 loosely. (3) Ignoring unit economics -- CAC/LTV matter even at seed. (4) Not segmenting by customer/channel/cohort. (5) Gaming metrics -- optimize for real outcomes.

## Investor Metrics

**Seed**: MRR growth rate, user retention, early unit economics, product engagement.
**Series A**: ARR + growth, CAC payback <18mo, LTV:CAC >3.0, NDR >100%, burn multiple <2.0.
**Series B+**: Rule of 40 >40%, efficient growth (magic number), path to profitability, market leadership.

**Dashboard Format**:
```
Current MRR: $250K (up 18% MoM)
ARR: $3.0M (up 280% YoY)
CAC: $1,200 | LTV: $4,800 | LTV:CAC = 4.0x
NDR: 112% | Logo Retention: 92%
Burn: $180K/mo | Runway: 18 months
```

Include: current value, growth rate/trend, context (target, benchmark).

## Quick Start

1. **Identify business model** -- SaaS, marketplace, consumer, B2B
2. **Choose 5-7 core metrics** based on stage and model
3. **Establish tracking** with analytics and dashboards
4. **Calculate unit economics** -- CAC, LTV, payback
5. **Set targets** using benchmarks
6. **Review regularly** -- weekly for core metrics
7. **Share with team** and update investors monthly/quarterly
