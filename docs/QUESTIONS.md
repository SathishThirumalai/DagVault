# 10 real questions my user will ask

Write them the way your user would type them. At least 3 must need more than one page to answer, and at least 1 must be a question your documents cannot answer.

| # | Question | Where the answer is (document, page) | Needs more than one page? |
|---|---|---|---|
| 1 | How do I isolate client-specific custom plugins so one client's DAG cannot import another client's plugin code? | airflow/plugins_manager.py, client_dags/tenant_isolation.py | Yes |
| 2 | How do I set up dynamic DAG generation from client configuration YAML files without triggering parse timeouts in the Airflow scheduler? | airflow/models/dagbag.py, client_dags/retail_client/dynamic_dag.py | Yes |
| 3 | Which Airflow executor should I use for retail batch jobs that require high task concurrency with Celery and Redis? | docs/apache-airflow/executor/celery.rst | No |
| 4 | How can I pass secure database credentials between tasks using Airflow Connections instead of hardcoding in DAG files? | airflow/models/connection.py, docs/apache-airflow/security.rst | Yes |
| 5 | What is the correct syntax for migrating legacy PythonOperator DAGs to the TaskFlow API with @task decorator in Airflow 2.x? | docs/apache-airflow/tutorial/taskflow.rst | No |
| 6 | How do I configure tenant-specific execution queues in CeleryExecutor to prevent healthcare DAG tasks from running on uncertified worker nodes? | airflow/config_templates/default_airflow.cfg, client_dags/healthcare_client/queues.py | Yes |
| 7 | Why is my DAG stuck in 'queued' state when max_active_runs_per_dag limit is reached? | airflow/models/dagrun.py | No |
| 8 | How do I configure SLA miss alert callbacks to notify specific client Slack channels on delayed pipeline completion? | airflow/models/slamiss.py, client_dags/sla_callbacks.py | Yes |
| 9 | What is the difference between data_interval_start and logical_date in Airflow 2.2+? | docs/apache-airflow/faq.rst | No |
| 10 | Can DagVault predict tomorrow's stock price for our retail client using deep learning? | (cannot be answered from my documents: DagVault is a code search and orchestration vault, not a financial forecasting tool) | none |
