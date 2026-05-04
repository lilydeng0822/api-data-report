import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import urllib.request
import pandas as pd

url = 'http://192.168.37.6:8087/practice_data?key=winlose'
req = urllib.request.Request(url)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))

rows = data.get('rows', [])
df = pd.DataFrame(rows)

df['profit'] = pd.to_numeric(df['profit'].str.replace(',', ''), errors='coerce').fillna(0)
df['allBet'] = pd.to_numeric(df['allBet'].str.replace(',', ''), errors='coerce').fillna(0)
df['roomType_upper'] = df['roomType'].str.upper()

grouped = df[df['roomType_upper'].isin(['K', 'PTK'])].groupby(['gameName', 'roomType_upper']).agg(
    total_bet=('allBet', 'sum'),
    total_profit=('profit', 'sum'),
    game_count=('allBet', 'count')
).reset_index()

grouped['win_rate_val'] = grouped.apply(lambda row: row['total_profit'] / row['total_bet'] if row['total_bet'] > 0 else 0, axis=1)
grouped['win_rate'] = grouped['win_rate_val'].apply(lambda x: f"{x:.2%}")
grouped['marker'] = grouped['win_rate_val'].apply(lambda x: '⭐正贏利' if x > 0 else '')

print('--- Grouped Data ---')
print(grouped.head(10))

warnings = []
filtered_df = df[df['roomType_upper'].isin(['K', 'PTK'])]
player_grouped = filtered_df.groupby('account').agg(
    total_bet=('allBet', 'sum'),
    total_profit=('profit', 'sum')
).reset_index()

for _, row in player_grouped.iterrows():
    if row['total_bet'] > 0 and row['total_profit'] > 0:
        win_rate = row['total_profit'] / row['total_bet']
        if win_rate > 0.05:
            warnings.append(f"Player {row['account']} win rate {win_rate:.2%} > 5%")

print('\n--- Warnings ---')
for w in warnings[:5]:
    print(w)

# Define translations for Sheet 1
translation_dict = {
    'walletType': '錢包類型',
    'gameEndTime': '遊戲結束時間',
    'account': '帳號',
    'opValue': '操作值',
    'gameId': '遊戲ID',
    'gameName': '遊戲名稱',
    'roomName': '房間名稱',
    'tableId': '桌號',
    'chairId': '座位號',
    'category': '分類',
    'language': '語言',
    'currency': '幣別',
    'gameNo': '遊戲局號',
    'banker': '莊家',
    'roomType': '房間類型',
    'allBet': '總押注',
    'revenue': '營收',
    'score': '得分',
    'cellScore': '底注',
    'profit': '盈虧',
    'roomType_upper': '房間類型(大寫)'
}
df_translated = df.rename(columns=translation_dict)

# Define translations for Sheet 2
grouped_translation = {
    'gameName': '遊戲名稱',
    'roomType_upper': '房間類型',
    'game_count': '局數',
    'total_bet': '總押注金額',
    'total_profit': '總盈虧金額',
    'win_rate': '勝率(利潤率)',
    'marker': '正贏利標記'
}
grouped_translated = grouped[['gameName', 'roomType_upper', 'game_count', 'total_bet', 'total_profit', 'win_rate', 'marker']].rename(columns=grouped_translation)

# Prepare dataframe for Sheet 3
all_players_grouped = df.groupby('account').agg(
    total_bet=('allBet', 'sum'),
    total_profit=('profit', 'sum'),
    game_count=('allBet', 'count')
).reset_index()

all_players_grouped['win_rate_val'] = all_players_grouped.apply(
    lambda row: row['total_profit'] / row['total_bet'] if row['total_bet'] > 0 else 0, axis=1
)
all_players_grouped['win_rate'] = all_players_grouped['win_rate_val'].apply(lambda x: f"{x:.2%}")
all_players_grouped['warning'] = all_players_grouped['win_rate_val'].apply(lambda x: '⚠大於5%' if x > 0.05 else '')

player_translation = {
    'account': '玩家帳號',
    'game_count': '局數',
    'total_bet': '總押注金額',
    'total_profit': '總盈虧金額',
    'win_rate': '勝率(營利率)',
    'warning': '超過5%標記'
}
player_sheet_df = all_players_grouped[['account', 'game_count', 'total_bet', 'total_profit', 'win_rate', 'warning']].rename(columns=player_translation)

# Output to Excel
excel_file = 'api_data_report.xlsx'
with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
    df_translated.to_excel(writer, sheet_name='API數據整理', index=False)
    grouped_translated.to_excel(writer, sheet_name='遊戲追放總表數據', index=False)
    player_sheet_df.to_excel(writer, sheet_name='玩家營利數據', index=False)

print(f'\n--- 成功匯出 ---')
print(f'已將資料匯出至: {excel_file}')
