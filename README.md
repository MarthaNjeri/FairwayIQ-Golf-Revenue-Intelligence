# 🏌️ FairwayIQ: Golf Club Management & Revenue Intelligence (AI + BI Project)

FairwayIQ is an end-to-end data science, business intelligence, and real-world software engineering project designed to transform golf club operations. It helps clubs maximize **member retention, revenue growth, and live tournament operational decision-making** using advanced data analytics, predictive machine learning, and dynamic application nodes.

This project consolidates membership engagement, real-time spending behavior, and churn risk signals into an executive-ready intelligence platform tailored for premium clubs (such as Limuru Country Club).

---

## 📌 Business Problem

Golf clubs generate vast, valuable data streams across membership subscriptions, tee-time activity, tournament engagement, and hospitality spending. However, most clubs lack an integrated analytics system to answer critical questions:

* Which members generate the highest lifetime value?
* What daily engagement or tournament behaviors predict churn risk?
* How can management bridge the gap between live on-course tournament play and clubhouse food & beverage (F&B) auxiliary revenue velocity?
* How can club committees leverage real-time data to optimize retention and profitability?

---

## 🎯 Project Goal

To build a **Unified Revenue & Membership Intelligence Platform** that enables club leadership to:

* ✅ **Understand Revenue Drivers:** Link on-course activities directly to clubhouse point-of-sale systems.
* ✅ **Segment Members by Value:** Track total member spend portfolios across all facilities.
* ✅ **Detect Early Churn Risk:** Leverage AI to identify at-risk behavioral markers before cancellation.
* ✅ **Optimize Live Operations:** Provide real-time leaderboard displays and frictionless digital scorecard pipelines.
* ✅ **Support Strategic Retention:** Drive data-backed decisions for the Club Secretary and Board of Directors.

---

## 🏗 System & Project Architecture

FairwayIQ is uniquely built as an event-driven, multi-port node workspace. This engineering approach guarantees 100% data stability and zero session conflicts by running isolated runtime threads that all sync to a unified project data lake:

* 🎛️ **Node 8500 (`hub.py`) | The Operations Cockpit:** The central administrative control room. Uses an iframe-embedding routing engine to cleanly switch between sub-consoles inside a single browser tab.
* 🏌️‍♂️ **Node 8501 (`scorecard_app.py`) | Player Scorecard Portal:** A live hole-by-hole score entry engine featuring R&A-compliant peer-verification (Flight Marker tracking).
* 🏆 **Node 8503 (`tournament_app.py`) | Championship Leaderboard Display:** A real-time spectator ranking board optimized for clubhouse TV displays, complete with gross/net sorting.
* 🍔 **Node 8505 (`fandb_app.py`) | Clubhouse F&B Terminal:** A hospitality point-of-sale terminal that pulls live field profiles directly from active golfer registries to track time-velocity spend metrics.

---

## 🔄 The Gate-to-Clubhouse Data Pipeline

FairwayIQ tracks the entire physical and financial journey of a golfer during a club fixture:By tracking the time interval between **Scorecard Verification** and **F&B Transaction Time**, the system generates deep business insights:
1. **Player Spending Velocity:** Pinpoints exactly when and where players convert tournament entry into auxiliary club revenue.
2. **Flight Pacing Analytics:** Tracks standard pacing intervals as flights transition past the 9th hole (Halfway House).
3. **Total Member Folio Value:** Unifies entry fees, golf handicaps, tournament performance, and hospitality bills under a single relational key (`MemberID`).

---

## 🧾 Dataset Overview & Relational Data Lake

Due to privacy constraints in private golf clubs, this project utilizes a combination of historical core databases alongside active live-event telemetry files to form its reporting foundation.

### Historical Core Tables
| File | Description |
|---|---|
| `members.csv` | Member demographics, enrollment dates, and membership tier details. |
| `play_activity.csv` | Historical golf rounds played, course tracking, and scoring history. |
| `engagement.csv` | Monthly aggregations of rounds, coaching lessons, and tournament entries. |
| `revenue.csv` | Record of annual membership subscriptions and historical auxiliary bills. |
| `member_status.csv` | Classification engine tags (`Active` / `At-Risk` / `Churned`) for ML training. |

### Real-Time Live Operations Files (Data Lake)
| File | Description | Key Relational Field |
|---|---|---|
| `data/live_leaderboard.csv` | The live tournament field pool, tracking player sign-ins from the gate scorecard node. | `MemberID` (Primary Key) |
| `data/pos_transactions.csv` | Granular clubhouse point-of-sale records containing split transaction dimensions. | `MemberID` (Foreign Key) |

---

## 📂 File Directory Tree

```bash
FairwayIQ/
│
├── data/                            # Relational Data Lake
│   ├── members.csv                  # Core Member Demographics
│   ├── revenue.csv                  # Historical Financial Logs
│   ├── engagement.csv               # Monthly Activity Metrics
│   ├── member_status.csv            # Active / At-Risk / Churned Labels
│   ├── live_leaderboard.csv         # Active Tournament Field Pool
│   └── pos_transactions.csv         # Split Live-POS Logs (PlayDate & PlayTime)
│
├── notebooks/                       # Data Science & Machine Learning Sandbox
│   ├── 01_FairwayIQ_EDA.ipynb       # Exploratory Analysis & Revenue Insights
│   └── 02_Churn_Prediction.ipynb   # Predictive Churn Modeling (Upcoming)
│
├── src/                             # Core ETL Logic
│   └── generate_fairwayiq_data.py   # Synthetic Pipeline Generation Script
│
├── output/                          # Machine Learning Pipeline Outputs
│   └── fairwayiq_ml_dataset.csv     # Engineered Modeling Dataset
│
├── hub.py                           # Master Dashboard Workspace Gateway (Port 8500)
├── scorecard_app.py                 # On-Course Player Score Stepper (Port 8501)
├── tournament_app.py                # Clubhouse TV Leaderboard Monitor (Port 8503)
├── fandb_app.py                     # Front-of-House Hospitality Console (Port 8505)
├── app.py                           # Legacy Core Initial Test Bed
├── .gitignore                       # Deployment Filter (Blocks private local tracking data)
├── requirements.txt                 # Project Dependencies Environment Setup
└── README.md                        # Project Portfolio Documentation
