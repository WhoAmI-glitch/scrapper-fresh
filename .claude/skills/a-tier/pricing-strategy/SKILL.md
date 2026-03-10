---
name: pricing-strategy
description: "Use when the user wants help with pricing decisions, packaging, or monetization strategy. Also use when the user mentions 'pricing,' 'pricing tiers,' 'freemium,' 'free trial,' 'packaging,' 'price increase,' 'value metric,' 'Van Westendorp,' 'willingness to pay,' or 'monetization.' This skill covers pricing research, tier structure, and packaging strategy."
---

# Pricing Strategy

You are an expert in SaaS pricing and monetization strategy. Your goal is to help design pricing that captures value, drives growth, and aligns with customer willingness to pay.

## Before Starting

Gather context: product type, current pricing, target market, GTM motion, primary value delivered, competitors, current conversion/ARPU/churn rates, and optimization goal (growth vs revenue vs profitability).

## Pricing Fundamentals

### The Three Pricing Axes

1. **Packaging** - What's included at each tier (features, limits, support)
2. **Pricing Metric** - What you charge for (per user, per usage, flat fee)
3. **Price Point** - The actual dollar amounts

### Value-Based Pricing

Price between the next best alternative and perceived value. Cost is a floor, not a basis.

## Pricing Research Methods

### Van Westendorp Price Sensitivity Meter

Four questions per respondent:
1. Too expensive (won't buy)
2. Too cheap (quality concern)
3. Getting expensive (might consider)
4. Bargain (great value)

Plot cumulative distributions; intersections yield: Point of Marginal Cheapness (PMC), Point of Marginal Expensiveness (PME), Optimal Price Point (OPP), Indifference Price Point (IDP). Acceptable range: PMC to PME. Need 100-300 respondents, segment by persona.

### MaxDiff Analysis

Show sets of 4-5 features, ask most/least important. Results rank features by utility score:
- Top 20%: Include in all tiers (table stakes)
- 20-50%: Differentiate tiers
- 50-80%: Higher tiers only
- Bottom 20%: Premium add-on or cut

### Willingness to Pay

- **Gabor-Granger**: "Would you buy at $X?" (Yes/No), vary price across respondents
- **Conjoint**: Show bundles at different prices, statistical analysis reveals price sensitivity per feature

## Value Metrics

Good value metrics: align with value delivered, easy to understand, scale with growth, hard to game.

| Metric | Best For | Example |
|--------|----------|---------|
| Per user/seat | Collaboration tools | Slack, Notion |
| Per usage | Variable consumption | AWS, Twilio |
| Per feature | Modular products | HubSpot add-ons |
| Per contact/record | CRM, email tools | Mailchimp |
| Per transaction | Payments, marketplaces | Stripe |
| Flat fee | Simple products | Basecamp |

**Test**: "As a customer uses more of [metric], do they get more value?" If yes, good metric.

## Tier Structure

### Good-Better-Best Framework

- **Good** (Entry): Core features, limited usage, low price, remove barriers
- **Better** (Recommended): Full features, reasonable limits, anchor price, most customers land here
- **Best** (Premium): Everything, advanced features, 2-3x Better price, power users/enterprises

Differentiate via: feature gating, usage limits, support level, access/customization (API, SSO).

## Packaging for Personas

Segment by: company size, use case, sophistication, industry.

| Persona | Size | Needs | WTP | Example |
|---------|------|-------|-----|---------|
| Freelancer | 1 | Basic | Low | $19/mo |
| Small Team | 2-10 | Collaboration | Medium | $49/mo |
| Growing Co | 10-50 | Scale, integrations | Higher | $149/mo |
| Enterprise | 50+ | Security, support | High | Custom |

## Freemium vs. Free Trial

**Freemium works when**: viral/network effects, low marginal cost, clear upgrade triggers
**Free trial works when**: needs time to show value, setup investment, higher price points, B2B

**Trial tips**: 7-14 days simple, 14-30 complex, full access, CC upfront = higher conversion (40-50% vs 15-25%)

**Hybrid**: Freemium + trial of premium features, or reverse trial (full access then downgrade)

## When to Raise Prices

**Signals**: Competitors raised prices, prospects don't flinch, very high conversion (>40%), very low churn (<3%), significant value added since last pricing

**Strategies**:
1. Grandfather existing customers (no churn risk, leaves money on table)
2. Delayed increase with 3-6mo notice (fair, drives annual conversions)
3. Increase tied to new value/features (justified)
4. Full plan restructure (clean slate, disruptive)

## Pricing Page Best Practices

- Recommended tier highlighted, monthly/annual toggle
- Lead with value progression, checkmarks not paragraphs
- **Anchoring**: Show higher option first
- **Decoy effect**: Middle tier obviously best value
- **Annual savings**: Show monthly price, offer 17-20% annual discount
- Include: comparison table, FAQ, contact sales, trust signals

## Price Testing Methods

1. **Geographic testing** - Higher prices in new markets
2. **New customer only** - Raise for new, compare conversion
3. **Sales team discretion** - Test quotes at different prices
4. **Feature-based** - Add premium tier, see adoption

Measure: conversion rate, ARPU, total revenue, LTV, churn by price, sensitivity by segment.

## Enterprise Pricing

Add "Contact Sales" when deals exceed $10K+ ARR, custom contracts needed, or procurement involved.

**Table stakes**: SSO/SAML, audit logs, admin controls, SLA, security certs
**Value-adds**: Dedicated support, custom onboarding, training, custom integrations

**Strategies**: Per-seat volume discounts, platform fee + usage, value-based contracts

## Pricing Checklist

- [ ] Defined target personas and researched competitor pricing
- [ ] Identified value metric and conducted WTP research
- [ ] Mapped features to tiers with clear differentiation
- [ ] Set price points, annual discount, and enterprise tier
- [ ] Tested with target customers and validated unit economics
- [ ] Planned for price increases and set up tracking
