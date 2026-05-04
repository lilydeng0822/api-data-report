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
    df['profit'] = pd.to_numeric(df['profit'].str.replace(',', ''), errors='coerce').fillna(0)
    df['allBet'] = pd.to_numeric(df['allBet'].str.replace(',', ''), errors='coerce').fillna(0)
    df['roomType_upper'] = df['roomType'].str.upper()
    return df

try:
    df = fetch_data()
    
    # 準備玩家營利率驗證的資料
    all_players_grouped = df.groupby('account').agg(
        total_bet=('allBet', 'sum'),
        total_profit=('profit', 'sum')
    ).reset_index()
    all_players_grouped['win_rate_val'] = all_players_grouped.apply(
        lambda row: row['total_profit'] / row['total_bet'] if row['total_bet'] > 0 else 0, axis=1
    )
    player_data = all_players_grouped.to_dict('records')
    
    # 準備 K/PTK 房間驗證的資料
    room_grouped = df[df['roomType_upper'].isin(['K', 'PTK'])].groupby(['gameName', 'roomType_upper']).agg(
        total_bet=('allBet', 'sum'),
        total_profit=('profit', 'sum')
    ).reset_index()
    room_grouped['win_rate_val'] = room_grouped.apply(
        lambda row: row['total_profit'] / row['total_bet'] if row['total_bet'] > 0 else 0, axis=1
    )
    room_data = room_grouped.to_dict('records')

except Exception as e:
    df = None
    player_data = []
    room_data = []

@allure.feature("遊戲資料數據處理與驗證報表")
class TestAPIData:

    @allure.story("1. 測試 API 資料連線與獲取")
    def test_api_connection(self):
        """
        測試 API 是否能正常連線並成功解析資料為 DataFrame。
        """
        assert df is not None, "無法從 API 獲取資料或解析失敗"
        assert not df.empty, "API 回傳的資料為空"
        allure.attach(str(len(df)), name="成功獲取的資料總筆數", attachment_type=allure.attachment_type.TEXT)

    @allure.story("2. 玩家營利率異常檢查")
    @allure.title("玩家 {player[account]} 營利率檢查")
    @pytest.mark.parametrize("player", player_data, ids=[p['account'] for p in player_data])
    def test_player_win_rate(self, player):
        """
        檢查玩家的贏錢比例是否超過 5%。
        如果不符合(大於 5%)，測試項目將標記為「失敗 (Failed)」，並顯示相關數據。
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
        
        # 斷言：營利率必須 <= 5%
        assert win_rate <= 0.05, f"異常！玩家 {account} 的營利率 {win_rate:.2%} 超過 5% 門檻！"

    @allure.story("3. K/PTK 房間類型正贏利標註")
    @allure.title("房間 {room[gameName]} ({room[roomType_upper]}) 贏利狀態")
    @pytest.mark.parametrize("room", room_data, ids=[f"{r['gameName']}-{r['roomType_upper']}" for r in room_data])
    def test_room_positive_win_rate(self, room):
        """
        檢視 K 和 PTK 類型的房間數據。
        若贏利率大於 0 (正數)，將在報表中標註為正贏利。
        """
        game = room['gameName']
        rtype = room['roomType_upper']
        total_bet = room['total_bet']
        total_profit = room['total_profit']
        win_rate = room['win_rate_val']
        
        info = (
            f"遊戲名稱: {game}\n"
            f"房間類型: {rtype}\n"
            f"總押注金額: {total_bet:.2f}\n"
            f"總盈虧金額: {total_profit:.2f}\n"
            f"勝率(利潤率): {win_rate:.2%}"
        )
        
        # 判斷是否為正贏利
        if win_rate > 0:
            info += "\n\n⭐ 【特別標註】 此為正贏利房間！"
            
        allure.attach(info, name="房間分析數據", attachment_type=allure.attachment_type.TEXT)
        
        # 確保有獲取到數據
        assert total_bet > 0, "此房間沒有任何押注紀錄"
