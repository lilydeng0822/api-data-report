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

df['profit'] = pd.to_numeric(df['profit'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
df['allBet'] = pd.to_numeric(df['allBet'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
df['roomType_upper'] = df['roomType'].str.upper()

exchange_rates = {
    "CNY": 1.0, "USD": 7.0, "TWD": 0.2, "MYR": 2.0, "VND": 0.0003,
    "THB": 0.2, "IDR": 0.0005, "JPY": 0.05, "AUD": 4.9, "EUR": 8.0,
    "GBP": 10.0, "INR": 0.1, "KRW": 0.006, "MMK": 0.005, "PHP": 0.2,
    "SGD": 4.8, "USDT": 6.0, "BRL": 1.4, "TRY": 2.0, "VNDK": 0.3,
    "RUB": 0.08, "IRR": 0.0001, "MMKK": 5.0, "NGN": 0.01, "IDRK": 0.5
}
df['exchangeRate'] = df['currency'].map(exchange_rates).fillna(1.0)
df['profit'] = df['profit'] * df['exchangeRate']
df['allBet'] = df['allBet'] * df['exchangeRate']

results = []
for game, group in df.groupby('gameName'):
    total_bet = group['allBet'].sum()
    total_profit = group['profit'].sum()
    total_count = group['allBet'].count()
    total_win_rate = total_profit / total_bet if total_bet > 0 else 0
    
    def get_room_stats(rtype):
        r_group = group[group['roomType_upper'] == rtype]
        bet = r_group['allBet'].sum()
        profit = r_group['profit'].sum()
        count = r_group['allBet'].count()
        wr = profit / bet if bet > 0 else 0
        return count, wr

    n_count, n_wr = get_room_stats('N')
    ptk_count, ptk_wr = get_room_stats('PTK')
    d_count, d_wr = get_room_stats('D')
    k_count, k_wr = get_room_stats('K')
    
    marker = []
    if ptk_wr > 0: marker.append("PTK營利率大於0")
    if k_wr > 0: marker.append("K營利率大於0")
    
    results.append({
        '遊戲': game,
        '總局數': total_count,
        '總盈利率': f"{total_win_rate:.2%}",
        'N局數': n_count,
        'N盈利率': f"{n_wr:.2%}",
        'ptk局數': ptk_count,
        'ptk盈利率': f"{ptk_wr:.2%}",
        'D局數': d_count,
        'D盈利率': f"{d_wr:.2%}",
        'K局數': k_count,
        'K盈利率': f"{k_wr:.2%}",
        '特別標註': " | ".join(marker)
    })

grouped_translated = pd.DataFrame(results)

print('--- Grouped Data ---')
print(grouped_translated.head(10))

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

# Sheet 2 data is already prepared in grouped_translated

# Prepare dataframe for Sheet 3
player_results = []
for account, group in df.groupby('account'):
    total_bet = group['allBet'].sum()
    total_profit = group['profit'].sum()
    total_count = group['allBet'].count()
    win_rate_val = total_profit / total_bet if total_bet > 0 else 0
    warning = '⚠大於-2.5%' if win_rate_val > -0.025 else ''
    
    def get_room_stats(rtype):
        r_group = group[group['roomType_upper'] == rtype]
        bet = r_group['allBet'].sum()
        profit = r_group['profit'].sum()
        count = r_group['allBet'].count()
        wr = profit / bet if bet > 0 else 0
        ratio = count / total_count if total_count > 0 else 0
        return count, wr, ratio

    n_count, n_wr, n_ratio = get_room_stats('N')
    ptk_count, ptk_wr, ptk_ratio = get_room_stats('PTK')
    d_count, d_wr, d_ratio = get_room_stats('D')
    k_count, k_wr, k_ratio = get_room_stats('K')
    
    player_results.append({
        '玩家帳號': account,
        '局數': total_count,
        '總押注金額': total_bet,
        '總盈虧金額': total_profit,
        '勝率(營利率)': f"{win_rate_val:.2%}",
        'RTP大於97.5': warning,
        'N局數': n_count,
        'N營利率': f"{n_wr:.2%}",
        'N局數比例': f"{n_ratio:.2%}",
        'PTK局數': ptk_count,
        'PTK營利率': f"{ptk_wr:.2%}",
        'PTK局數比例': f"{ptk_ratio:.2%}",
        'D局數': d_count,
        'D營利率': f"{d_wr:.2%}",
        'D局數比例': f"{d_ratio:.2%}",
        'K局數': k_count,
        'K營利率': f"{k_wr:.2%}",
        'K局數比例': f"{k_ratio:.2%}"
    })

player_sheet_df = pd.DataFrame(player_results)

# Output to Excel
excel_file = 'api_data_report.xlsx'
with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
    df_translated.to_excel(writer, sheet_name='API數據整理', index=False)
    grouped_translated.to_excel(writer, sheet_name='遊戲追放總表數據', index=False)
    player_sheet_df.to_excel(writer, sheet_name='玩家營利數據', index=False)

print(f'\n--- 成功匯出 ---')
print(f'已將資料匯出至: {excel_file}')
