# DagVault

## Problem

Data engineering consultants at a Chennai consultancy maintain Apache Airflow pipelines for multiple retail and healthcare clients. Consultants switch between clients throughout the day and need to search both the public Airflow workflow engine and the private code belonging to the client they are currently working with. Existing code-search and GenAI systems can accidentally mix information from different clients. DagVault provides unified search across public Airflow code and authorized client repositories while ensuring that one client's private code is never exposed to another client.

## Who it is for

- Data engineering consultants working with multiple retail and healthcare clients.
- Engineering teams that maintain Apache Airflow pipelines, DAGs, and plugins for multiple clients.

## Signature feature

Secure multi-tenant code search that combines the shared open-source Apache Airflow codebase with the private DAGs and plugins of the currently authorized client, while strictly isolating private code between clients.

## Hardest problem (my interview story)

The hardest problem is maintaining strict tenant isolation while still providing useful GenAI answers. A consultant should be able to ask a question that requires both public Apache Airflow knowledge and their client's private DAGs or plugins, but the retrieval system must never retrieve another client's private files.

