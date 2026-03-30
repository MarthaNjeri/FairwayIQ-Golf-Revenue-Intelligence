# 🏌️ FairwayIQ: Golf Club Management & Revenue Intelligence (AI + BI Project)

FairwayIQ is an end-to-end data science and business intelligence project designed to help golf clubs improve **member retention, revenue growth, and operational decision-making** using analytics and machine learning.

This project consolidates membership engagement, spending behavior, and churn risk signals into an executive-ready intelligence platform.

---

## 📌 Business Problem

Golf clubs generate valuable data across:

- Membership subscriptions  
- Tee-time activity  
- Coaching participation  
- Tournament engagement  
- Pro shop and food & beverage spending  

However, most clubs lack an integrated analytics system to answer key questions such as:

- Which members generate the highest lifetime value?
- What engagement behaviors predict churn risk?
- How does playing frequency impact revenue?
- How can management optimize retention and club profitability?

---

## 🎯 Project Goal

To build a **Revenue & Membership Intelligence Platform** that enables club leadership to:

✅ Understand revenue drivers  
✅ Segment members by value and engagement  
✅ Detect early churn risk  
✅ Support strategic retention initiatives  
✅ Leverage AI for predictive decision-making  

---

## 🧾 Dataset Overview (Synthetic + Realistic)

Due to privacy constraints in private golf clubs, this project uses **synthetic data generated based on real-world golf club operations**, including realistic engagement and revenue patterns.

### Tables Generated

| File | Description |
|------|------------|
| `members.csv` | Member demographics and membership tier |
| `play_activity.csv` | Golf rounds and score activity |
| `engagement.csv` | Monthly rounds, coaching, tournaments |
| `revenue.csv` | Membership fees + spending behavior |
| `member_status.csv` | Active / At-Risk / Churned labels |

---

## 🏗 Project Structure

```bash
FairwayIQ/
│
├── data/
│   ├── members.csv
│   ├── revenue.csv
│   ├── engagement.csv
│   ├── member_status.csv
│
├── notebooks/
│   ├── 01_FairwayIQ_EDA.ipynb
│   ├── 02_Churn_Prediction.ipynb   # upcoming
│
├── src/
│   ├── generate_fairwayiq_data.py
│
├── output/
│   ├── fairwayiq_ml_dataset.csv
│
├── README.md
└── requirements.txt
# Golf-Club-Management-Revenue-Intelligence-AI-BI-Project-
---

## 📊 Live Dashboard

You can view the interactive Power BI dashboard here:

🔗 **FairwayIQ Live Dashboard:**  
https://app.powerbi.com/view?r=eyJrIjoiYzMzYjA2ODEtYWUzNy00ZTYyLWI3MjMtZTM0Y2QzOWVhZWIwIiwidCI6ImNjZWM4MmJhLTA1OTctNDRjNy1hODM4LTEzNjIwY2MxZGJlYiJ9

> This dashboard presents membership engagement, revenue analysis, retention insights, and churn risk indicators for golf club management decision-making.

---

