# 🌿 Wildlife Conservation Research Network

> A multi-site conservation platform where the database is the application — stored procedures, recursive CTEs, triggers, partitioned tables, and window functions built around a real conservation science domain.

A full-stack desktop system managing a network of wildlife sanctuary sites, built with Python and MySQL. Animal genetic lineage is tracked through self-referencing parentage — enabling recursive pedigree queries that detect inbreeding before a breeding pair is ever approved. Behavioral field observations accumulate as a partitioned time-series, analysed entirely through window functions. Every critical workflow — admitting an animal, transferring it between facilities, administering treatment — is an atomic stored procedure with SAVEPOINT-level rollback control.

## Key Features

- 🧬 Recursive pedigree CTE — walks ancestor trees to block genetically incompatible breeding pairs at the DB layer
- 📊 Behavioral time-series analytics — `RANK`, `LAG`, rolling `AVG` window functions over partitioned observation data
- ⚡ Table partitioning — `observations` range-partitioned by year, with `EXPLAIN PARTITIONS` live in the UI
- 🔄 Stored procedures — 6 atomic multi-table workflows with full `SAVEPOINT` transaction control
- 🔔 9 triggers — `BEFORE INSERT` eligibility guards, auto-quarantine on incidents, contraindication checking
- 📅 MySQL Events — annual partition maintenance, weekly health sweeps, nightly expiry checks
- 🗂️ 7 views — sick animal roster, zone occupancy, active treatments, breeding program status
- 🔍 Full-text search — field observation notes indexed and searchable across the research portal
- 🔐 Audit log — append-only, trigger-populated change history with JSON old/new value snapshots
- 👥 Role-based access — Admin, Veterinarian, Researcher, Caretaker with per-module permissions

## Tech Stack

| Layer | Technology |
|---|---|
| Database | MySQL 8.0+ |
| Language | Python 3.10+ |
| GUI | Tkinter |
| Driver | mysql-connector-python |
| Auth | SHA-256 password hashing |

## Schema

| | |
|---|---|
| Tables | 20 |
| Relationships | 38 |
| Self-referencing FKs | 2 (`father_id`, `mother_id` on `animals`) |
| Partitioned tables | 1 (`observations` — `RANGE` by `YEAR`) |
| JSON columns | 3 (species weights, medicine contraindications, audit snapshots) |
| Indexes | 9 (composite, single-column, full-text) |

ER diagram → paste [`docs/er_diagram.dbml`](docs/er_diagram.dbml) into [dbdiagram.io](https://dbdiagram.io)

## Setup

```bash
git clone https://github.com/your-username/wcrn.git && cd wcrn
pip install mysql-connector-python
mysql -u root -p -e "CREATE DATABASE wcrn CHARACTER SET utf8mb4;"
mysql -u root -p wcrn < schema.sql
mysql -u root -p wcrn < seed_data.sql
cp .env.example .env   # add your MySQL credentials
python wcrn.py
```
