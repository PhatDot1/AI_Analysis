# Loads your AI usage and user directory logs

# Computes AI‐adoption rates by team

# Finds the highest- and lowest-adopting teams

# Tracks month-over-month adoption to surface any stagnant/declining teams

# Flags individual users whose AI usage hasn’t grown (or has dropped)

import pandas as pd
import matplotlib.pyplot as plt

# load relevant data
users = pd.read_csv('data/user_directory.csv', parse_dates=['join_date'])
ai    = pd.read_csv('data/ai_usage_logs.csv',   parse_dates=['date'])

# a) i) adoption by team
adopt = (
    ai
    .groupby('team')['used_ai_tool']
    .agg(total_tasks='count', ai_tasks=lambda x: x.sum())
    .assign(adoption_rate=lambda df: df['ai_tasks']/df['total_tasks']*100)
    .reset_index()
)
print("\n💡 AI Adoption Rate by Team:")
print(adopt.to_string(index=False))

# a) ii) highest & lowest
high = adopt.loc[adopt['adoption_rate'].idxmax()]
low  = adopt.loc[adopt['adoption_rate'].idxmin()]
print(f"\n🔺 Highest adoption: {high.team} ({high.adoption_rate:.1f}%)")
print(f"🔻 Lowest  adoption: {low.team} ({low.adoption_rate:.1f}%)")

# a) iii) monthly adoption trend per team
ai['month'] = ai['date'].dt.to_period('M')
monthly = ai.groupby(['team','month'])['used_ai_tool'].mean().reset_index()

trend = (
    monthly
    .sort_values(['team','month'])
    .groupby('team')
    .agg(
        first_rate=('used_ai_tool','first'),
        last_rate =('used_ai_tool','last')
    )
    .assign(change_pct=lambda df: (df['last_rate'] - df['first_rate']) * 100)
    .reset_index()
)
print("\n📈 Adoption Trend (First vs Last Month) by Team:")
print(trend.to_string(index=False))

# a) iii) teams flat or declining
stagnant = trend[trend['change_pct'] <= 0]
print("\n⚠️ Teams with Stagnant/Declining Adoption:")
print(stagnant.to_string(index=False))

# a) iii) identify users with stagnant/declining usage
user_monthly = ai.groupby(['user_id','month'])['used_ai_tool'].mean().reset_index()
user_trend = (
    user_monthly
    .sort_values(['user_id','month'])
    .groupby('user_id')
    .agg(
        first_rate=('used_ai_tool','first'),
        last_rate =('used_ai_tool','last')
    )
    .assign(change_pct=lambda df: (df['last_rate'] - df['first_rate']) * 100)
    .reset_index()
)

# attach user names & teams
user_team = ai.groupby('user_id')['team'].agg(lambda s: s.mode().iloc[0]).reset_index()
user_trend = (
    user_trend
    .merge(user_team, on='user_id')
    .merge(users[['user_id','full_name']], on='user_id')
)
decliners = user_trend[user_trend['change_pct'] <= 0]
print("\n⚠️ Users with Stagnant/Declining AI Adoption:")
print(decliners.to_string(index=False))

# plot adoption rates
plt.figure()
plt.bar(adopt['team'], adopt['adoption_rate'])
plt.title('AI Adoption Rate by Team')
plt.xlabel('Team')
plt.ylabel('Adoption Rate (%)')
plt.tight_layout()
plt.show()
