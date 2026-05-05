import json
import urllib.request
import pandas as pd

def generate_report():
    url = 'http://192.168.37.6:8087/practice_data?key=winlose'
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        rows = data.get('rows', [])
        df = pd.DataFrame(rows)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

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

    # Process game data
    game_results = []
    for game, group in df.groupby('gameName'):
        total_bet = float(group['allBet'].sum())
        total_profit = float(group['profit'].sum())
        total_count = int(group['allBet'].count())
        total_win_rate = total_profit / total_bet if total_bet > 0 else 0
        
        def get_room_stats(rtype):
            r_group = group[group['roomType_upper'] == rtype]
            bet = float(r_group['allBet'].sum())
            profit = float(r_group['profit'].sum())
            count = int(r_group['allBet'].count())
            wr = profit / bet if bet > 0 else 0
            ratio = count / total_count if total_count > 0 else 0
            return count, wr, ratio

        n_count, n_wr, n_ratio = get_room_stats('N')
        ptk_count, ptk_wr, ptk_ratio = get_room_stats('PTK')
        d_count, d_wr, d_ratio = get_room_stats('D')
        k_count, k_wr, k_ratio = get_room_stats('K')
        
        marker = []
        if ptk_wr > 0: marker.append("PTK營利率大於0")
        if k_wr > 0: marker.append("K營利率大於0")
        
        game_results.append({
            'game': game,
            'total_count': total_count,
            'total_profit_rate': total_win_rate,
            'n_count': n_count, 'n_profit_rate': n_wr, 'n_ratio': n_ratio,
            'ptk_count': ptk_count, 'ptk_profit_rate': ptk_wr, 'ptk_ratio': ptk_ratio,
            'd_count': d_count, 'd_profit_rate': d_wr, 'd_ratio': d_ratio,
            'k_count': k_count, 'k_profit_rate': k_wr, 'k_ratio': k_ratio,
            'marker': " | ".join(marker)
        })

    # Process player data
    player_results = []
    for account, group in df.groupby('account'):
        total_bet = float(group['allBet'].sum())
        total_profit = float(group['profit'].sum())
        total_count = int(group['allBet'].count())
        win_rate_val = total_profit / total_bet if total_bet > 0 else 0
        warning = '⚠大於-2.5%' if win_rate_val > -0.025 else ''
        
        def get_room_stats(rtype):
            r_group = group[group['roomType_upper'] == rtype]
            bet = float(r_group['allBet'].sum())
            profit = float(r_group['profit'].sum())
            count = int(r_group['allBet'].count())
            wr = profit / bet if bet > 0 else 0
            ratio = count / total_count if total_count > 0 else 0
            return count, wr, ratio

        n_count, n_wr, n_ratio = get_room_stats('N')
        ptk_count, ptk_wr, ptk_ratio = get_room_stats('PTK')
        d_count, d_wr, d_ratio = get_room_stats('D')
        k_count, k_wr, k_ratio = get_room_stats('K')
        
        player_results.append({
            'account': account,
            'total_count': total_count,
            'total_bet': total_bet,
            'total_profit': total_profit,
            'total_profit_rate': win_rate_val,
            'warning': warning,
            'n_count': n_count, 'n_profit_rate': n_wr, 'n_ratio': n_ratio,
            'ptk_count': ptk_count, 'ptk_profit_rate': ptk_wr, 'ptk_ratio': ptk_ratio,
            'd_count': d_count, 'd_profit_rate': d_wr, 'd_ratio': d_ratio,
            'k_count': k_count, 'k_profit_rate': k_wr, 'k_ratio': k_ratio
        })

    html_template = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>互動式營利數據報表</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f172a;
            --panel-bg: rgba(30, 41, 59, 0.7);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: rgba(255, 255, 255, 0.1);
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --danger: #ef4444;
            --success: #10b981;
        }}
        body {{
            background: linear-gradient(135deg, var(--bg-color) 0%, #1e1b4b 100%);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 40px;
            min-height: 100vh;
        }}
        h1, h2 {{
            font-weight: 800;
            margin-bottom: 24px;
            text-align: center;
            background: -webkit-linear-gradient(45deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        .section {{
            background: var(--panel-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        .controls {{
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            justify-content: center;
        }}
        input, select, button {{
            padding: 12px 20px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            font-size: 16px;
            outline: none;
            background: rgba(15, 23, 42, 0.5);
            color: white;
            transition: all 0.3s ease;
        }}
        input:focus, select:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
        }}
        button {{
            background: var(--accent);
            color: white;
            font-weight: 600;
            cursor: pointer;
            border: none;
        }}
        button:hover {{
            background: var(--accent-hover);
            transform: translateY(-2px);
        }}
        .table-container {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            margin-top: 16px;
        }}
        th, td {{
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            white-space: nowrap;
        }}
        th {{
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 14px;
            letter-spacing: 0.05em;
        }}
        tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}
        .clickable {{
            color: #60a5fa;
            cursor: pointer;
            font-weight: bold;
            transition: color 0.3s;
        }}
        .clickable:hover {{
            color: #93c5fd;
        }}
        .expandable-row {{
            display: none;
            background: rgba(0, 0, 0, 0.2) !important;
        }}
        .expandable-row.active {{
            display: table-row;
            animation: fadeIn 0.4s ease-in-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .chart-container {{
            display: flex;
            gap: 40px;
            padding: 32px;
            align-items: center;
            justify-content: center;
        }}
        .pie-box {{
            width: 300px;
            height: 300px;
        }}
        .stats-box table {{
            width: auto;
            margin: 0;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            overflow: hidden;
        }}
        .stats-box th, .stats-box td {{
            padding: 12px 24px;
            border: none;
            border-bottom: 1px solid var(--border-color);
        }}
        .positive {{ color: var(--success); font-weight: 600; }}
        .negative {{ color: var(--danger); font-weight: 600; }}
        .warning-badge {{
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            border: 1px solid rgba(239, 68, 68, 0.4);
        }}
        .total-profit-display {{
            margin-top: 20px;
            font-size: 18px;
            font-weight: 600;
            text-align: center;
            padding: 12px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 互動式營利數據報表</h1>

        <!-- 第一區塊：遊戲統計數據 -->
        <div class="section">
            <h2>遊戲統計數據</h2>
            <div class="controls">
                <select id="gameSelect">
                    <option value="all">全部遊戲</option>
                </select>
                <button onclick="filterGames()">搜尋遊戲</button>
            </div>
            <div class="table-container">
                <table id="gameTable">
                    <thead>
                        <tr>
                            <th>遊戲</th>
                            <th>總局數</th>
                            <th>總營利率</th>
                            <th>N局數</th>
                            <th>N營利率</th>
                            <th>PTK局數</th>
                            <th>PTK營利率</th>
                            <th>D局數</th>
                            <th>D營利率</th>
                            <th>K局數</th>
                            <th>K營利率</th>
                            <th>特別標註</th>
                        </tr>
                    </thead>
                    <tbody id="gameTableBody"></tbody>
                </table>
            </div>
        </div>

        <!-- 第二區塊：玩家營利數據 -->
        <div class="section">
            <h2>玩家營利數據</h2>
            <div class="controls">
                <input type="text" id="playerSearch" placeholder="搜尋玩家名稱..." onkeypress="if(event.key === 'Enter') filterPlayers()">
                <button onclick="filterPlayers()">搜尋玩家</button>
            </div>
            <div class="table-container">
                <table id="playerTable">
                    <thead>
                        <tr>
                            <th>玩家帳號</th>
                            <th>局數</th>
                            <th>總押注金額</th>
                            <th>總盈虧金額</th>
                            <th>勝率(營利率)</th>
                            <th>RTP大於97.5</th>
                            <th>N局數</th>
                            <th>N營利率</th>
                            <th>N局數比例</th>
                            <th>PTK局數</th>
                            <th>PTK營利率</th>
                            <th>PTK局數比例</th>
                            <th>D局數</th>
                            <th>D營利率</th>
                            <th>D局數比例</th>
                            <th>K局數</th>
                            <th>K營利率</th>
                            <th>K局數比例</th>
                        </tr>
                    </thead>
                    <tbody id="playerTableBody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const gameData = {json.dumps(game_results)};
        const playerData = {json.dumps(player_results)};
        const chartInstances = {{}};

        function formatPercent(val) {{ return (val * 100).toFixed(2) + '%'; }}
        function formatNumber(val) {{ return val.toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}}); }}
        function getColorClass(val) {{ return val > 0 ? 'positive' : (val < 0 ? 'negative' : ''); }}

        let currentGameView = [];
        let currentPlayerView = [];

        function renderGamesFiltered(data) {{
            currentGameView = data;
            const tbody = document.getElementById('gameTableBody');
            tbody.innerHTML = '';
            data.forEach((d, idx) => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="clickable" onclick="toggleRow('game', ${{idx}})">${{d.game}} ▼</td>
                    <td>${{d.total_count}}</td>
                    <td class="${{getColorClass(d.total_profit_rate)}}">${{formatPercent(d.total_profit_rate)}}</td>
                    <td>${{d.n_count}}</td>
                    <td class="${{getColorClass(d.n_profit_rate)}}">${{formatPercent(d.n_profit_rate)}}</td>
                    <td>${{d.ptk_count}}</td>
                    <td class="${{getColorClass(d.ptk_profit_rate)}}">${{formatPercent(d.ptk_profit_rate)}}</td>
                    <td>${{d.d_count}}</td>
                    <td class="${{getColorClass(d.d_profit_rate)}}">${{formatPercent(d.d_profit_rate)}}</td>
                    <td>${{d.k_count}}</td>
                    <td class="${{getColorClass(d.k_profit_rate)}}">${{formatPercent(d.k_profit_rate)}}</td>
                    <td>${{d.marker ? `<span class="warning-badge">${{d.marker}}</span>` : ''}}</td>
                `;
                tbody.appendChild(tr);

                const expandTr = document.createElement('tr');
                expandTr.id = `game-expand-${{idx}}`;
                expandTr.className = 'expandable-row';
                expandTr.innerHTML = `
                    <td colspan="12">
                        <div class="chart-container">
                            <div class="pie-box"><canvas id="game-chart-${{idx}}"></canvas></div>
                            <div class="stats-box">
                                <table>
                                    <tr><th>房間類型</th><th>局數</th><th>比例</th></tr>
                                    <tr><td>N</td><td>${{d.n_count}}</td><td>${{formatPercent(d.n_ratio)}}</td></tr>
                                    <tr><td>PTK</td><td>${{d.ptk_count}}</td><td>${{formatPercent(d.ptk_ratio)}}</td></tr>
                                    <tr><td>D</td><td>${{d.d_count}}</td><td>${{formatPercent(d.d_ratio)}}</td></tr>
                                    <tr><td>K</td><td>${{d.k_count}}</td><td>${{formatPercent(d.k_ratio)}}</td></tr>
                                </table>
                            </div>
                        </div>
                    </td>
                `;
                tbody.appendChild(expandTr);
            }});
        }}

        function renderPlayersFiltered(data) {{
            currentPlayerView = data;
            const tbody = document.getElementById('playerTableBody');
            tbody.innerHTML = '';
            data.forEach((d, idx) => {{
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="clickable" onclick="toggleRow('player', ${{idx}})">${{d.account}} ▼</td>
                    <td>${{d.total_count}}</td>
                    <td>${{formatNumber(d.total_bet)}}</td>
                    <td class="${{getColorClass(d.total_profit)}}">${{formatNumber(d.total_profit)}}</td>
                    <td class="${{getColorClass(d.total_profit_rate)}}">${{formatPercent(d.total_profit_rate)}}</td>
                    <td>${{d.warning ? `<span class="warning-badge">${{d.warning}}</span>` : ''}}</td>
                    <td>${{d.n_count}}</td>
                    <td class="${{getColorClass(d.n_profit_rate)}}">${{formatPercent(d.n_profit_rate)}}</td>
                    <td>${{formatPercent(d.n_ratio)}}</td>
                    <td>${{d.ptk_count}}</td>
                    <td class="${{getColorClass(d.ptk_profit_rate)}}">${{formatPercent(d.ptk_profit_rate)}}</td>
                    <td>${{formatPercent(d.ptk_ratio)}}</td>
                    <td>${{d.d_count}}</td>
                    <td class="${{getColorClass(d.d_profit_rate)}}">${{formatPercent(d.d_profit_rate)}}</td>
                    <td>${{formatPercent(d.d_ratio)}}</td>
                    <td>${{d.k_count}}</td>
                    <td class="${{getColorClass(d.k_profit_rate)}}">${{formatPercent(d.k_profit_rate)}}</td>
                    <td>${{formatPercent(d.k_ratio)}}</td>
                `;
                tbody.appendChild(tr);

                const expandTr = document.createElement('tr');
                expandTr.id = `player-expand-${{idx}}`;
                expandTr.className = 'expandable-row';
                expandTr.innerHTML = `
                    <td colspan="18">
                        <div class="chart-container">
                            <div class="pie-box"><canvas id="player-chart-${{idx}}"></canvas></div>
                            <div class="stats-box">
                                <table>
                                    <tr><th>房間類型</th><th>局數</th><th>比例</th></tr>
                                    <tr><td>N</td><td>${{d.n_count}}</td><td>${{formatPercent(d.n_ratio)}}</td></tr>
                                    <tr><td>PTK</td><td>${{d.ptk_count}}</td><td>${{formatPercent(d.ptk_ratio)}}</td></tr>
                                    <tr><td>D</td><td>${{d.d_count}}</td><td>${{formatPercent(d.d_ratio)}}</td></tr>
                                    <tr><td>K</td><td>${{d.k_count}}</td><td>${{formatPercent(d.k_ratio)}}</td></tr>
                                </table>
                                <div class="total-profit-display">該玩家總營利率: <span class="${{getColorClass(d.total_profit_rate)}}">${{formatPercent(d.total_profit_rate)}}</span></div>
                            </div>
                        </div>
                    </td>
                `;
                tbody.appendChild(expandTr);
            }});
        }}

        function toggleRow(type, idx) {{
            const row = document.getElementById(`${{type}}-expand-${{idx}}`);
            row.classList.toggle('active');
            if(row.classList.contains('active')) {{
                const d = type === 'game' ? currentGameView[idx] : currentPlayerView[idx];
                renderChart(`${{type}}-chart-${{idx}}`, d);
            }}
        }}

        function renderChart(canvasId, d) {{
            if(chartInstances[canvasId]) return;
            
            const ctx = document.getElementById(canvasId).getContext('2d');
            const counts = [d.n_count, d.ptk_count, d.d_count, d.k_count];
            if(counts.every(c => c === 0)) counts[0] = 0.0001; 

            chartInstances[canvasId] = new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: ['N', 'PTK', 'D', 'K'],
                    datasets: [{{
                        data: counts,
                        backgroundColor: [
                            '#3b82f6', 
                            '#10b981', 
                            '#f59e0b', 
                            '#8b5cf6'  
                        ],
                        borderWidth: 0,
                        hoverOffset: 10
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ position: 'right', labels: {{ color: '#f8fafc', font: {{ size: 14 }} }} }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const val = context.raw < 1 ? 0 : context.raw;
                                    return ` ${{context.label}}: ${{val}} 局`;
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        function filterGames() {{
            const val = document.getElementById('gameSelect').value;
            if(val === 'all') renderGamesFiltered(gameData);
            else renderGamesFiltered(gameData.filter(g => g.game === val));
        }}

        function filterPlayers() {{
            const val = document.getElementById('playerSearch').value.toLowerCase();
            if(!val) renderPlayersFiltered(playerData);
            else renderPlayersFiltered(playerData.filter(p => p.account.toLowerCase().includes(val)));
        }}

        window.onload = () => {{
            const select = document.getElementById('gameSelect');
            [...new Set(gameData.map(d => d.game))].forEach(game => {{
                select.add(new Option(game, game));
            }});
            renderGamesFiltered(gameData);
            renderPlayersFiltered(playerData);
        }};
    </script>
</body>
</html>
"""

    with open('interactive_report.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    print("Interactive HTML report generated at interactive_report.html")

if __name__ == '__main__':
    generate_report()
