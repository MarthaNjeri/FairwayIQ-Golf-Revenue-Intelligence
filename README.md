# 🏌️ FairwayIQ: Golf Club Management & Revenue Intelligence (AI + BI Project)

FairwayIQ is an end-to-end data science, business intelligence, and real-world software engineering platform designed to transform golf club operations. It helps clubs maximize **member retention, auxiliary revenue growth, and live tournament operational decision-making** using advanced data analytics, predictive machine learning, and dynamic, multi-role application nodes.

This project consolidates membership engagement, real-time spending behavior, and churn risk signals into an executive-ready intelligence platform tailored specifically for the unique landscape of **Kenyan Golf Clubs** (such as Limuru Country Club, Karen Country Club, and Muthaiga Golf Club).

---

## 📌 Business Problem

Golf clubs generate vast, valuable data streams across membership subscriptions, tee-time activity, tournament engagement, and hospitality spending. However, most clubs lack an integrated analytics system to answer critical questions:

* Which members generate the highest lifetime value (LTV)?
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
* ✅ **Eliminate On-Course F&B Friction:** Introduce predictive turn-times and on-course pickup locations to match pace of play.

---

## 🏗 System & Project Architecture

FairwayIQ is built as a unified, session-stable Streamlit multi-portal workspace driven by a single entry point (`app.py`). This engineering approach guarantees 100% data stability and zero session conflicts by isolating user views based on roles, all syncing to a unified SQLite relational database:

* 🏌️‍♂️ **Player Scorecard Portal:** A live hole-by-hole score entry engine featuring R&A-compliant peer-verification (Flight Marker tracking), integrated with the **38 KGU-affiliated golf clubs** across Kenya (Nairobi, Mt. Kenya, Central Rift, Coast, Western, and North Rift regions).
* 🍔 **Clubhouse F&B Terminal:** A predictive hospitality point-of-sale terminal that pulls live field profiles directly from active golfer registries to track time-velocity spend metrics. Includes **live stock auto-depletion warnings**, **COGS tracking**, and **Predictive Turn-Prep ETAs**.
* 🏆 **Tournament Leaderboard Monitor:** A real-time spectator ranking board optimized for clubhouse TV displays, complete with gross/net sorting.
* 🛡️ **Kachumbari Admin Control Center:** Behind-the-scenes control panel for captains and directors. Handles daily check-ins, generates dynamic matches/pairings, handles handicap overrides, calculates round podiums, and drives a live **3-Hole Playoff Shootout** bracket.

---

## 🔄 The Gate-to-Clubhouse Data Pipeline

FairwayIQ tracks the entire physical and financial journey of a golfer during a club fixture:
[ Gate Entry ] ──> [ Check-in / Player Portal ] ──> [ On-Course Play & Scorecard Verification ]
│
▼
[ Advanced Hospitality Analytics ] <── [ Predictive F&B Terminal / Steward Performance POS ]


By tracking the time interval between **Scorecard Verification** and **F&B Transaction Time**, the system generates deep business insights:
1. **Player Spending Velocity:** Pinpoints exactly when and where players convert tournament entry into auxiliary club revenue.
2. **Pace-of-Play Kitchen Optimization:** Flags orders destined for "Hole 9 Turn" or "Hole 10 Tee" to ensure food is prepared hot exactly as the flight transitions.
3. **Steward Metrics:** Tracks sales volume and gross revenue per waiter to gamify staffing and optimize peak hours.
4. **Total Member Folio Value:** Unifies entry fees, golf handicaps, tournament performance, and hospitality bills under a single relational key (`MemberID`).

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
| `data/pos_transactions.csv` | Granular clubhouse point-of-sale records containing split transaction dimensions, COGS metrics, and steward assignments. | `MemberID` (Foreign Key) |

---

## 📂 File Directory Tree

```bash
FairwayIQ/
│
├── core/                            # 🧠 BACKEND PROCESSORS & DATABASE CORES
│   ├── __init__.py                  # Python Module Marker
│   ├── database.py                  # Relational Schema Migrations & DB Threads
│   └── scoring_engine.py            # SQL Points Aggregation & Score Submissions
│
├── views/                           # 📊 FRONT-END STREAMLIT TERMINAL VIEWS
│   ├── __init__.py                  # Python Module Marker
│   ├── scorecard_terminal.py        # Player Score Input, KGU Database & Tournaments
│   ├── fandb_terminal.py            # Hospitality POS Terminal, COGS & turn-prep
│   ├── leaderboard.py               # Combined Season Standings & TV Monitor 
│   ├── admin_panel.py               # Unified pairings engine, Captain overrides & shootout
│   ├── roster_manager.py            # External CSV / Google Sheets Sync Pipeline
│   └── course_manager.py            # Dynamic Course Directory Setup
│
├── data/                            # 💾 LOCAL SECURE DATA CORES
│   ├── fairway_iq.db                # SQLite Relational Database Binary File
│   ├── live_leaderboard.csv         # Legacy Live Tournament Stream Fallback
│   └── pos_transactions.csv         # Auxiliary Clubhouse Spend Transaction Logs
│
├── notebooks/                       # 🔬 DATA SCIENCE & PREDICTIVE ANALYTICS
│   ├── 01_FairwayIQ_EDA.ipynb       # Exploratory Analysis & Revenue Insights
│   └── 02_Churn_Prediction.ipynb    # Predictive Machine Learning Churn Models
│
├── src/                             # ⚙️ DATA ENGINEERING & PIPELINES
│   └── generate_fairwayiq_data.py   # Synthetic Historical Generation Engine
│
├── output/                          # 📦 ENGINERED MODELLING STORAGE
│   └── fairwayiq_ml_dataset.csv     # Transformed ML Processing Frame
│
├── app.py                           # 🚀 Central Hub & Unified Workspace Controller
├── .gitignore                       # Deployment Environmental Filter
├── README.md                        # Portfolio Engineering Documentation
└── requirements.txt                 # Project Dependencies Manifest