# Architecture

## System Architecture
This project follows a modular research structure with clear separation between source code, experiments, notebooks, and tests.

## Mermaid Diagram
`mermaid
flowchart TD
  A[datasets/] --> B[src/]
  B --> C[experiments/]
  B --> D[tests/]
  C --> E[docs/results.md]
  F[scripts/] --> B
  G[notebooks/] --> C
`
"@

     = @"
# Methodology

## Algorithms
Document algorithm choices and model variants under this section.

## Datasets
Describe data collection, preprocessing, and splits.

## Evaluation Metrics
Define task-specific metrics and reproducibility settings.