import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

print(f"⏳ [ pipeline ] Starting automated intelligence refresh at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 1. Dynamically map production folder paths
# 1. Dynamically map production folder paths safely
script_dir = os.path.dirname(os.path.abspath(__file__))

# If the script lives inside the notebooks folder, step up one level to find the true root
if "notebooks" in script_dir:
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
else:
    project_root = script_dir

data_dir = os.path.join(project_root, "data")

try:
    # 2. Ingest the latest operational club files
    print("📥 [ pipeline ] Reading raw operational datasets...")
    df_members = pd.read_csv(os.path.join(data_dir, 'members.csv'))
    df_engagement = pd.read_csv(os.path.join(data_dir, 'engagement.csv'))
    df_revenue = pd.read_csv(os.path.join(data_dir, 'revenue.csv'))
    df_status = pd.read_csv(os.path.join(data_dir, 'member_status.csv'))

    # 3. Aggregate metrics (Feature Engineering)
    print("⚙️ [ pipeline ] Processing member behavioral features...")
    activity_summary = df_engagement.groupby('MemberID').agg(
        TotalRounds=('RoundsPlayed', 'sum'),
        AvgMonthlyRounds=('RoundsPlayed', 'mean')
    ).reset_index()

    recent_activity = df_engagement[df_engagement['Month'] == 6][['MemberID', 'RoundsPlayed']].rename(
        columns={'RoundsPlayed': 'RecentMonthRounds'}
    )

    # Compile the consolidated matrix
    df_ml = pd.merge(df_members, activity_summary, on='MemberID', how='inner')
    df_ml = pd.merge(df_ml, recent_activity, on='MemberID', how='inner')
    df_ml = pd.merge(df_ml, df_revenue, on='MemberID', how='inner')
    df_ml = pd.merge(df_ml, df_status, on='MemberID', how='inner')
    df_ml['TotalSpend'] = df_ml['SubscriptionFee'] + df_ml['AncillarySpend']

    # 4. Spin up a fresh training instance for the predictions
    # Dropping non-predictive columns
    X = df_ml.drop(columns=['MemberID', 'PlayerName', 'ChurnStatus'])
    
    # In a full production app, you could load a saved model (.pkl file) here. 
    # For our lean setup, retraining on the fly takes less than a second!
    from sklearn.ensemble import RandomForestClassifier
    print("🧠 [ pipeline ] Recalculating AI risk weights...")
    ai_engine = RandomForestClassifier(n_estimators=100, random_state=42)
    ai_engine.fit(X, df_ml['ChurnStatus'])

    # 5. Append fresh Churn Scores
    df_ml['Churn_Probability_%'] = (ai_engine.predict_proba(X)[:, 1] * 100).round(1)
    df_ml['Risk_Level'] = pd.cut(
        df_ml['Churn_Probability_%'], 
        bins=[-1, 30, 70, 100], 
        labels=['Low Risk', 'Medium Risk', 'High Risk']
    )

    # 6. Build the Power BI payload format
    power_bi_export = df_ml[[
        'MemberID', 'PlayerName', 'Handicap', 'JoinYear', 
        'TotalRounds', 'RecentMonthRounds', 'TotalSpend', 
        'Churn_Probability_%', 'Risk_Level'
    ]]

    # Overwrite the pipeline dashboard source file
    export_path = os.path.join(data_dir, 'power_bi_churn_analysis.csv')
    power_bi_export.to_csv(export_path, index=False)
    
    print(f"✅ [ pipeline ] Pipeline execution successful! New insights compiled for Power BI.")
    print(f"📊 Live Tracked Members: {len(power_bi_export)} | High Risk Flagged: {len(power_bi_export[power_bi_export['Risk_Level']=='High Risk'])}")

except Exception as e:
    print(f"❌ [ pipeline ERROR ] Refresh pipeline failed to execute: {str(e)}")