# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from src.core.xml_reader import get_player_node
from src.core.reference_data import load_object_map
from src.modules.player import parse_player
from src.modules.shipping import parse_shipping
from src.modules.fishing import parse_fishing
from src.modules.museum import parse_museum
from src.modules.cooking import parse_cooking
from src.modules.social import parse_social

SAVE_DIR = Path(os.getenv("SAVE_DIR", "/saves"))
OUTPUT_HTML = Path("index.html")

def find_all_saves(saves_dir):
    """Scan SAVE_DIR for all valid Stardew Valley save files."""
    save_files = []
    if not saves_dir.exists():
        return save_files
        
    for item in saves_dir.iterdir():
        if item.is_dir():
            target_file = item / item.name
            if target_file.exists() and not item.name.startswith("."):
                save_files.append((item.name, target_file))
    return sorted(save_files, key=lambda x: x[0])

def analyze_save(file_path):
    root, player = get_player_node(file_path)
    
    data = parse_player(player)
    data["shipped_items"] = parse_shipping(player)
    data["fish_caught"] = parse_fishing(player)
    data["museum_pieces"] = parse_museum(root)
    data["recipes_cooked"] = parse_cooking(player)
    data["friendships"] = parse_social(player)
    
    return data

def generate_dashboard_html(all_saves_data, object_map):
    def sort_key(item_tuple):
        key = item_tuple[0] if isinstance(item_tuple, tuple) else item_tuple
        return (0, int(key)) if str(key).isdigit() else (1, str(key))

    save_tabs_html = []
    save_views_html = []

    for idx, (save_id, data) in enumerate(all_saves_data.items()):
        is_active = "active" if idx == 0 else ""
        display_style = "block" if idx == 0 else "none"

        # Build top save switchers
        save_tabs_html.append(
            f'<button class="save-tab {is_active}" onclick="switchSave(\'{save_id}\', event)">'
            f'{data["farm"]} ({data["farmer"]})</button>'
        )

        # Build rows for each tab
        shipped_rows = []
        for item_id, count in sorted(data["shipped_items"].items(), key=sort_key):
            clean_id = str(item_id).replace("(O)", "")
            item_name = object_map.get(str(item_id)) or object_map.get(clean_id) or str(item_id)
            shipped_rows.append(f"<tr><td><code>{item_id}</code></td><td><b>{item_name}</b></td><td>{count}</td></tr>")

        fish_rows = []
        for item_id, stats in sorted(data["fish_caught"].items(), key=sort_key):
            clean_id = str(item_id).replace("(O)", "")
            item_name = object_map.get(str(item_id)) or object_map.get(clean_id) or str(item_id)
            fish_rows.append(f"<tr><td><code>{item_id}</code></td><td><b>{item_name}</b></td><td>{stats['count']}</td><td>{stats['length']} in.</td></tr>")

        museum_rows = []
        for item_id in sorted(data["museum_pieces"], key=sort_key):
            clean_id = str(item_id).replace("(O)", "")
            item_name = object_map.get(str(item_id)) or object_map.get(clean_id) or str(item_id)
            museum_rows.append(f"<tr><td><code>{item_id}</code></td><td><b>{item_name}</b></td></tr>")

        cooking_rows = []
        for item_id, count in sorted(data["recipes_cooked"].items(), key=sort_key):
            clean_id = str(item_id).replace("(O)", "")
            item_name = object_map.get(str(item_id)) or object_map.get(clean_id) or str(item_id)
            cooking_rows.append(f"<tr><td><code>{item_id}</code></td><td><b>{item_name}</b></td><td>{count}</td></tr>")

        social_rows = []
        for npc_name, info in data["friendships"].items():
            heart_str = f"<b>{info['hearts']}</b> / {info['max_hearts']} Hearts ({info['points']} pts)"
            talked_badge = "<span style='color:#10b981;'>Yes</span>" if info['talked_today'] else "<span style='color:#ef4444;'>No</span>"
            status_badge = f"<span style='color:#f59e0b;'>{info['status']}</span>" if info['status'] != 'Friendly' else info['status']
            
            social_rows.append(
                f"<tr><td><b>{npc_name}</b></td>"
                f"<td>{heart_str}</td>"
                f"<td>{info['gifts_this_week']} / 2</td>"
                f"<td>{talked_badge}</td>"
                f"<td>{status_badge}</td></tr>"
            )

        save_views_html.append(f"""
        <div id="save-view-{save_id}" class="save-view" style="display: {display_style};">
            <div class="header-card">
                <div class="header-title">
                    <h1>{data['farm']} Farm</h1>
                    <div class="gold-badge">G: {data['money']:,} g</div>
                </div>
                <div class="stats-grid">
                    <div class="stat-box"><div class="label">Farmer</div><div class="val">{data['farmer']}</div></div>
                    <div class="stat-box"><div class="label">Total Gold Earned</div><div class="val">{data['total_earned']:,} g</div></div>
                    <div class="stat-box"><div class="label">Items Shipped</div><div class="val">{len(data['shipped_items'])}</div></div>
                    <div class="stat-box"><div class="label">Fish Caught</div><div class="val">{len(data['fish_caught'])}</div></div>
                    <div class="stat-box"><div class="label">Museum Pieces</div><div class="val">{len(data['museum_pieces'])}</div></div>
                    <div class="stat-box"><div class="label">Recipes Cooked</div><div class="val">{len(data['recipes_cooked'])}</div></div>
                    <div class="stat-box"><div class="label">Villagers Met</div><div class="val">{len(data['friendships'])}</div></div>
                </div>
            </div>

            <div class="nav-tabs">
                <button class="tab-btn active" onclick="switchTab('{save_id}', 'shipping', event)">Shipped Items</button>
                <button class="tab-btn" onclick="switchTab('{save_id}', 'fishing', event)">Fishing</button>
                <button class="tab-btn" onclick="switchTab('{save_id}', 'museum', event)">Museum</button>
                <button class="tab-btn" onclick="switchTab('{save_id}', 'cooking', event)">Cooking</button>
                <button class="tab-btn" onclick="switchTab('{save_id}', 'social', event)">Social / Villagers</button>
            </div>

            <div id="tab-{save_id}-shipping" class="tab-content active">
                <h2>Shipped Items Register ({len(data['shipped_items'])})</h2>
                <table>
                    <thead><tr><th>ID</th><th>Item Name</th><th>Quantity Shipped</th></tr></thead>
                    <tbody>{''.join(shipped_rows) if shipped_rows else '<tr><td colspan="3">No shipped items</td></tr>'}</tbody>
                </table>
            </div>

            <div id="tab-{save_id}-fishing" class="tab-content">
                <h2>Fish Caught Log ({len(data['fish_caught'])})</h2>
                <table>
                    <thead><tr><th>ID</th><th>Fish Name</th><th>Count Caught</th><th>Record Size</th></tr></thead>
                    <tbody>{''.join(fish_rows) if fish_rows else '<tr><td colspan="4">No fish caught</td></tr>'}</tbody>
                </table>
            </div>

            <div id="tab-{save_id}-museum" class="tab-content">
                <h2>Museum Collection ({len(data['museum_pieces'])})</h2>
                <table>
                    <thead><tr><th>ID</th><th>Donated Item Name</th></tr></thead>
                    <tbody>{''.join(museum_rows) if museum_rows else '<tr><td colspan="2">No museum pieces donated</td></tr>'}</tbody>
                </table>
            </div>

            <div id="tab-{save_id}-cooking" class="tab-content">
                <h2>Recipes Cooked ({len(data['recipes_cooked'])})</h2>
                <table>
                    <thead><tr><th>ID</th><th>Recipe / Dish Name</th><th>Times Cooked</th></tr></thead>
                    <tbody>{''.join(cooking_rows) if cooking_rows else '<tr><td colspan="3">No recipes cooked</td></tr>'}</tbody>
                </table>
            </div>

            <div id="tab-{save_id}-social" class="tab-content">
                <h2>Villager Friendships ({len(data['friendships'])})</h2>
                <table>
                    <thead><tr><th>Villager</th><th>Friendship Level</th><th>Gifts This Week</th><th>Talked Today</th><th>Status</th></tr></thead>
                    <tbody>{''.join(social_rows) if social_rows else '<tr><td colspan="5">No villagers met</td></tr>'}</tbody>
                </table>
            </div>
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stardew Save Analyzer</title>
    <style>
        :root {{
            --bg-main: #0f172a;
            --bg-card: #1e293b;
            --bg-border: #334155;
            --accent: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 24px;
            background: var(--bg-main);
            color: var(--text-main);
            max-width: 1100px;
            margin: 0 auto;
        }}
        .saves-bar {{
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--bg-border);
            padding-bottom: 8px;
            flex-wrap: wrap;
        }}
        .save-tab {{
            background: #0f172a;
            border: 1px solid var(--bg-border);
            color: var(--text-muted);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 0.85em;
            cursor: pointer;
            font-weight: 600;
        }}
        .save-tab.active {{
            background: var(--bg-border);
            color: var(--accent);
            border-color: var(--accent);
        }}
        .header-card {{
            background: var(--bg-card);
            border: 1px solid var(--bg-border);
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 24px;
        }}
        .header-title {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            border-bottom: 1px solid var(--bg-border);
            padding-bottom: 12px;
        }}
        .header-title h1 {{
            margin: 0;
            color: var(--accent);
            font-size: 1.8em;
        }}
        .gold-badge {{
            font-size: 1.1em;
            font-weight: bold;
            color: #10b981;
            background: #064e3b;
            padding: 6px 12px;
            border-radius: 20px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 16px;
        }}
        .stat-box {{
            background: #0f172a;
            padding: 12px 16px;
            border-radius: 6px;
            border: 1px solid var(--bg-border);
        }}
        .stat-box .label {{
            font-size: 0.8em;
            color: var(--text-muted);
            text-transform: uppercase;
        }}
        .stat-box .val {{
            font-size: 1.3em;
            font-weight: bold;
            margin-top: 4px;
        }}
        .nav-tabs {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .tab-btn {{
            background: var(--bg-card);
            border: 1px solid var(--bg-border);
            color: var(--text-muted);
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }}
        .tab-btn.active {{
            background: var(--accent);
            color: #0f172a;
            border-color: var(--accent);
        }}
        .tab-content {{
            display: none;
            background: var(--bg-card);
            border: 1px solid var(--bg-border);
            border-radius: 10px;
            padding: 20px;
        }}
        .tab-content.active {{
            display: block;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 12px 16px;
            border-bottom: 1px solid var(--bg-border);
        }}
        th {{
            background: #0f172a;
            color: var(--accent);
            font-size: 0.9em;
        }}
        code {{
            background: #0f172a;
            padding: 2px 6px;
            border-radius: 4px;
            color: #38bdf8;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="saves-bar">
        {''.join(save_tabs_html)}
    </div>

    {''.join(save_views_html)}

    <script>
        function switchSave(saveId, evt) {{
            document.querySelectorAll('.save-view').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.save-tab').forEach(el => el.classList.remove('active'));
            document.getElementById('save-view-' + saveId).style.display = 'block';
            evt.currentTarget.classList.add('active');
        }}

        function switchTab(saveId, tabName, evt) {{
            const activeSave = document.getElementById('save-view-' + saveId);
            activeSave.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            activeSave.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + saveId + '-' + tabName).classList.add('active');
            evt.currentTarget.classList.add('active');
        }}
    </script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Successfully generated dashboard for {len(all_saves_data)} save(s) at {OUTPUT_HTML.resolve()}")

if __name__ == "__main__":
    object_map = load_object_map()
    saves = find_all_saves(SAVE_DIR)
    
    all_saves_data = {}
    for save_id, save_path in saves:
        try:
            all_saves_data[save_id] = analyze_save(save_path)
        except Exception as e:
            print(f"[WARN] Failed to parse save '{save_id}': {e}")
            
    if all_saves_data:
        generate_dashboard_html(all_saves_data, object_map)
    else:
        print(f"[WARN] No valid saves found in {SAVE_DIR.resolve()}")
