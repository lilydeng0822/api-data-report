import pytest
import allure
import json
import urllib.request
import pandas as pd

# 從 API 獲取資料並轉為 DataFrame
def fetch_data():
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
    return df

try:
    df = fetch_data()
    
    # 準備【單個遊戲】營利率驗證的資料
    game_grouped = df.groupby('gameName').agg(
        total_bet=('allBet', 'sum'),
        total_profit=('profit', 'sum')
    ).reset_index()
    game_grouped['win_rate_val'] = game_grouped.apply(
        lambda row: row['total_profit'] / row['total_bet'] if row['total_bet'] > 0 else 0, axis=1
    )
    game_data = game_grouped.to_dict('records')

    # 準備【單個玩家】營利率驗證的資料
    all_players_grouped = df.groupby('account').agg(
        total_bet=('allBet', 'sum'),
        total_profit=('profit', 'sum')
    ).reset_index()
    all_players_grouped['win_rate_val'] = all_players_grouped.apply(
        lambda row: row['total_profit'] / row['total_bet'] if row['total_bet'] > 0 else 0, axis=1
    )
    player_data = all_players_grouped.to_dict('records')
    
except Exception as e:
    df = None
    game_data = []
    player_data = []

@allure.feature("遊戲與玩家營利率自動化測試報表")
class TestAPIData:

    @allure.story("1. 測試 API 資料連線與獲取")
    def test_api_connection(self):
        """
        測試 API 是否能正常連線並成功解析資料為 DataFrame。
        """
        assert df is not None, "無法從 API 獲取資料或解析失敗"
        assert not df.empty, "API 回傳的資料為空"
        allure.attach(str(len(df)), name="成功獲取的資料總筆數", attachment_type=allure.attachment_type.TEXT)

    @allure.story("2. 單個遊戲總營利率檢測")
    @allure.title("遊戲 {game[gameName]} 營利率檢查")
    @pytest.mark.parametrize("game", game_data, ids=[g['gameName'] for g in game_data])
    def test_game_profit_rate(self, game):
        """
        檢查單個遊戲的總營利率是否大於 -2.5%。
        如果不符合 (<= -2.5%)，測試項目將標記為「失敗 (Failed)」。
        """
        game_name = game['gameName']
        total_bet = game['total_bet']
        total_profit = game['total_profit']
        win_rate = game['win_rate_val']
        
        # 附加詳細數據供報表檢視
        details = (
            f"遊戲名稱: {game_name}\n"
            f"總押注金額: {total_bet:.2f}\n"
            f"總盈虧金額: {total_profit:.2f}\n"
            f"勝率(營利率): {win_rate:.2%}"
        )
        allure.attach(details, name="遊戲詳細數據", attachment_type=allure.attachment_type.TEXT)
        
        # 斷言：營利率必須 > -2.5% (-0.025)
        assert win_rate > -0.025, f"異常！遊戲 {game_name} 的營利率 {win_rate:.2%} 小於等於 -2.5% 門檻！"

    @allure.story("3. 單個玩家總營利率檢測")
    @allure.title("玩家 {player[account]} 營利率檢查")
    @pytest.mark.parametrize("player", player_data, ids=[p['account'] for p in player_data])
    def test_player_profit_rate(self, player):
        """
        檢查單個玩家的總營利率是否大於 -2.5%。
        如果不符合 (<= -2.5%)，測試項目將標記為「失敗 (Failed)」。
        """
        account = player['account']
        total_bet = player['total_bet']
        total_profit = player['total_profit']
        win_rate = player['win_rate_val']
        
        # 附加詳細數據供報表檢視
        details = (
            f"玩家帳號: {account}\n"
            f"總押注金額: {total_bet:.2f}\n"
            f"總盈虧金額: {total_profit:.2f}\n"
            f"勝率(營利率): {win_rate:.2%}"
        )
        allure.attach(details, name="玩家詳細數據", attachment_type=allure.attachment_type.TEXT)
        
        # 斷言：營利率必須 > -2.5% (-0.025)
        assert win_rate > -0.025, f"異常！玩家 {account} 的營利率 {win_rate:.2%} 小於等於 -2.5% 門檻！"
