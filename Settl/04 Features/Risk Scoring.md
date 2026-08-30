# Risk Scoring

## Purpose

Estimate the probability that a revenue-loss case will be successfully recovered.

## Features

- amount
- event type
- failure reason
- attempt count
- customer success rate
- customer value
- previous recovery success rate
- time since event
- opt-out status

## Formula

Expected Recovery Value:

`amount_at_risk × recovery_probability`

## Model

Start with Logistic Regression.

Do not use an LLM to invent probabilities.

## Track

- model version
- feature version
- probability
- prediction timestamp
