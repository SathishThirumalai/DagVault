# Dataset

## Dataset Overview

DagVault uses Apache Airflow source code as the shared public dataset and five synthetic client repositories created from Apache Airflow public example DAGs.

The dataset is designed for a multi-tenant code-search system where public Airflow code can be searched together with a selected client's private repository without exposing another client's data.

## Dataset Sources

| Dataset | Description | Files | Access Scope | Licence / Terms |
|---|---|---:|---|---|
| Apache Airflow | Public Apache Airflow source repository from GitHub | 15,090 | Shared / Public | Apache-2.0 |
| Client Retail | Synthetic client repository based on Airflow public example DAGs | 54 | Private tenant | Based on Apache-2.0 public examples + synthetic files |
| Client Healthcare | Synthetic client repository based on Airflow public example DAGs | 53 | Private tenant | Based on Apache-2.0 public examples + synthetic files |
| Client Finance | Synthetic client repository based on Airflow public example DAGs | 52 | Private tenant | Based on Apache-2.0 public examples + synthetic files |
| Client Logistics | Synthetic client repository based on Airflow public example DAGs | 52 | Private tenant | Based on Apache-2.0 public examples + synthetic files |
| Client E-commerce | Synthetic client repository based on Airflow public example DAGs | 52 | Private tenant | Based on Apache-2.0 public examples + synthetic files |

## Source Repository

**Apache Airflow**

Source: https://github.com/apache/airflow

The complete repository was downloaded and stored under:

`data/raw/apache_airflow/`

The repository contains Airflow source code, example DAGs, tests, documentation, configuration files and other project files.

## Client Repositories

Five synthetic client repositories were created:

```text
data/raw/
├── apache_airflow/
├── client_retail/
├── client_healthcare/
├── client_finance/
├── client_logistics/
└── client_ecommerce/
```

Each client repository contains:

- `dags/` — Airflow DAG examples
- `plugins/` — synthetic client-specific plugin/configuration files
- `metadata.json` — tenant metadata and access scope

The client repositories are **synthetic samples**, not real confidential customer repositories. Public Apache Airflow example DAGs were copied and organized into separate tenant directories to simulate private client repositories.

## Dataset Size

The dataset contains more than the required **9,900 source files** across the shared Airflow repository and synthetic client repositories.

Source-like files were counted using:

```text
.py
.sql
.sh
.yaml
.yml
.js
.ts
```

Final source-file count:

**9,900+ source files**

Total files across `data/raw/`, including documentation and other repository files:

**15,353 files**

## Tenant Isolation

The dataset represents the following tenant structure:

```text
Shared public data
└── Apache Airflow

Private tenant data
├── client_retail
├── client_healthcare
├── client_finance
├── client_logistics
└── client_ecommerce
```

The intended DagVault behavior is that a user working with one client can retrieve:

1. Shared Apache Airflow source code
2. The selected client's private code

but cannot retrieve another client's private repository.

## Data Status

- [x] Apache Airflow source downloaded
- [x] Five synthetic client repositories created
- [x] Client DAGs and plugins added
- [x] Tenant metadata added
- [x] 9,900+ source-file requirement reached
- [x] Dataset added to Git repository
- [x] Dataset pushed to GitHub
- [ ] Dataset indexing / search pipeline
- [ ] Tenant-aware retrieval
- [ ] Access-control validation
- [ ] Final application integration

## Notes

The full dataset is stored in:

`data/raw/`

The dataset is committed to the DagVault GitHub repository for the current project stage.