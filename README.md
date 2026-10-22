# DagVault

## Problem
Data engineering consultants at a Chennai consultancy maintain Apache Airflow pipelines for multiple retail and healthcare clients. Consultants switch between clients throughout the day and need answers that combine the public Apache Airflow code with each client's private DAGs and plugins. The challenge is that private code from one client must never be exposed to another client. DagVault provides searchable access to the shared Airflow code and the currently authorized client's private repositories while maintaining strict separation between clients.

## Who it is for
Data engineering consultants at a Chennai consultancy who maintain Apache Airflow pipelines for multiple retail and healthcare clients.

## Signature feature
A secure multi-tenant code search system that combines public Apache Airflow source code with the private DAGs and plugins of the authorized client without leaking code across clients.

## Hardest problem (my interview story)
The hardest problem is ensuring strict tenant isolation while still allowing consultants to get useful answers that combine public Airflow code with their client's private code. The system must make sure that when a consultant is working with one client, retrieval can access the shared public Airflow code and that client's private repository, but can never retrieve another client's private code.

## Dataset
| Source | Link | Documents | Pages | Licence / terms |
|---|---|---:|---:|---|
| Apache Airflow source code | https://github.com/apache/airflow | 9,900+ source files | N/A | Apache-2.0 |
| Sample client repositories | Created from Apache Airflow public example DAGs | 3–5 separate client repositories | N/A | Based on Apache-2.0 licensed public examples |

## 10 real questions
See [docs/QUESTIONS.md](docs/QUESTIONS.md).

## Run it


## Live link
<Added in Week 2>
