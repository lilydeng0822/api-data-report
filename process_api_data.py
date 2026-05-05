import urllib.request
import json
import os

def process_data():
    url = "http://192.168.37.6:8087/practice_data?key=usermoney"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        
        records = data.get('rows', [])
        
        all_processed = []
        
        for current in records:
            # Format orderType to Traditional Chinese
            order_type_map = {
                "游戏投注": "遊戲投注",
                "游戏结算": "遊戲結算",
                "现金网上分": "現金網上分",
                "现金网下分": "現金網下分",
                "活动彩金": "活動彩金",
                "代理返水": "代理返水"
            }
            raw_type = current.get('orderType', '')
            translated_type = order_type_map.get(raw_type, raw_type)
            
            processed_row = {
                '紀錄ID': current.get('id', ''),
                '玩家帳號': current.get('playerAccount', 'Unknown'),
                '交易時間': current.get('orderTime', ''),
                '交易類型': translated_type,
                '帳變前金額': current.get('curScore', ''),
                '交易金額': current.get('addScore', ''),
                '帳變後金額': current.get('newScore', '')
            }
            all_processed.append(processed_row)
            
        # Sort all processed by time DESC (newest first) for display
        all_processed.sort(key=lambda x: x['交易時間'], reverse=True)
        
        # Generate Markdown
        md_lines = ["# 帳變明細數據整理報告\n"]
        md_lines.append(f"共處理了 **{len(all_processed)}** 筆數據。\n")
        
        md_lines.append("## 📄 最新 100 筆帳變紀錄預覽\n")
        md_lines.append("| 紀錄ID | 玩家帳號 | 交易時間 | 交易類型 | 帳變前金額 | 交易金額 | 帳變後金額 |")
        md_lines.append("|---|---|---|---|---|---|---|")
        for r in all_processed[:100]:
            md_lines.append(f"| {r['紀錄ID']} | {r['玩家帳號']} | {r['交易時間']} | {r['交易類型']} | {r['帳變前金額']} | {r['交易金額']} | {r['帳變後金額']} |")

        with open("usermoney_report.md", "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        print(f"Total processed: {len(all_processed)}")
        print("Markdown report saved to usermoney_report.md")
        
        # Also generate an HTML file for the full report
        html_lines = [
            "<html><head><meta charset='utf-8'><title>帳變數據報表</title>",
            "<style>",
            "body { font-family: sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            "</style></head><body>",
            "<h1>帳變明細數據整理報表</h1>",
            f"<p>總計處理數據：{len(all_processed)} 筆</p>"
        ]
        
        html_lines.append("<h2>完整帳變紀錄</h2>")
        html_lines.append("<table><tr><th>紀錄ID</th><th>玩家帳號</th><th>交易時間</th><th>交易類型</th><th>帳變前金額</th><th>交易金額</th><th>帳變後金額</th></tr>")
        for r in all_processed:
            html_lines.append(f"<tr><td>{r['紀錄ID']}</td><td>{r['玩家帳號']}</td><td>{r['交易時間']}</td><td>{r['交易類型']}</td><td>{r['帳變前金額']}</td><td>{r['交易金額']}</td><td>{r['帳變後金額']}</td></tr>")
        html_lines.append("</table></body></html>")
        
        with open("usermoney_report.html", "w", encoding="utf-8") as f:
            f.write("\n".join(html_lines))
        print("HTML report saved to usermoney_report.html")

        # --- EXCEL EXPORT ---
        try:
            import pandas as pd
            
            # Create DataFrames
            df_all = pd.DataFrame(all_processed)
            # Reorder columns for the main report
            df_all = df_all[['紀錄ID', '玩家帳號', '交易時間', '交易類型', '帳變前金額', '交易金額', '帳變後金額']]
            
            with pd.ExcelWriter("usermoney_report.xlsx", engine="openpyxl") as writer:
                df_all.to_excel(writer, sheet_name="完整帳變紀錄", index=False)
            print("Excel report saved to usermoney_report.xlsx")
        except ImportError:
            print("pandas or openpyxl not installed. Skipping Excel export.")

    except Exception as e:
        print(f"Error processing data: {e}")

if __name__ == '__main__':
    process_data()
