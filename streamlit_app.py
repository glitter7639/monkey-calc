import streamlit as st
import math

# --- 1. 翻訳対策 & ページ設定 ---
st.set_page_config(page_title="期待値算出エンジン Pro [モンキーV]", layout="centered")

st.components.v1.html(
    """
    <script>
        window.parent.document.documentElement.setAttribute('lang', 'ja');
        window.parent.document.documentElement.setAttribute('class', 'notranslate');
    </script>
    """,
    height=0,
)

# --- 2. パスワード認証システム（ここを追加） ---
# ※ noteで購入したユーザーに伝えるパスワードをここに設定してください
CORRECT_PASSWORD = "763983" 

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔑 有料会員専用ページ")
    st.write("このページを表示するには、noteで発行されたパスワードを入力してください。")
    password_input = st.text_input("パスワードを入力", type="password")
    if st.button("認証"):
        if password_input == CORRECT_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが正しくありません。")
    st.stop() # 認証されるまで以下のコードを実行させない

# --- 3. 認証後のメインコンテンツ（ここから下は元のコードを維持） ---

# --- サイドバー（機種・ホール設定） ---
with st.sidebar:
    st.header("🎰 機種・ホール設定")
    # カスタム入力を削除し、モンキー固定に
    machine_select = "スマスロ モンキーターンV"
    st.info(f"ターゲット機種: {machine_select}")
    
    st.divider()

    monkey_full_data = {
        "1": {"hit": "1/299.8", "rate": "97.9%",  "h_val": 299.8, "r_val": 97.9},
        "2": {"hit": "1/295.5", "rate": "98.9%",  "h_val": 295.5, "r_val": 98.9},
        "3": {"hit": "1/276.5", "rate": "101.0%", "h_val": 276.5, "r_val": 101.0},
        "4": {"hit": "1/258.8", "rate": "104.5%", "h_val": 258.8, "r_val": 104.5},
        "5": {"hit": "1/235.7", "rate": "110.2%", "h_val": 235.7, "r_val": 110.2},
        "6": {"hit": "1/222.9", "rate": "114.9%", "h_val": 222.9, "r_val": 114.9}
    }

    st.subheader("📊 モンキー専用 公表値")
    selected_setting = st.radio("設定選択", ["1", "2", "3", "4", "5", "6"], horizontal=True)
    d = monkey_full_data[selected_setting]
    
    st.info(f"設定{selected_setting}\n\n初当り\n{d['hit']}\n\n機械割\n{d['rate']}")
    conf_hit = d['h_val']
    conf_rate = d['r_val']
    
    st.divider()
    kashidashi_mai = st.selectbox("貸出枚数 (1kあたり)", [50, 47, 46], index=2)
    koukan_rate = st.number_input("交換率 (1kあたりの回収枚数)", value=5.2, step=0.1)

st.title(f"🛡️ {machine_select}")

# --- 3. 初期値設定（モンキー専用に固定） ---
d_base = 32.3
d_target_g = 795
d_exp_out = 485
d_c1_pt = 222 
d_c6_pt = 444
d_normal_pt = 666

# --- 4. モンキー専用：状況選択 ---
st.subheader("🕵️ モンキー専用：状況選択")
m_col1, m_col2 = st.columns(2)

with m_col1:
    # 1. 状態選択（リセット・青島後か通常か）
    m_condition = st.radio("天井設定", ["通常時 (795G)", "リセット/青島VS波多野敗北後 (495G)"])
    
    # 2. ヘルメットロゴ選択
    m_helmet = st.selectbox("ヘルメットロゴ", [
        "なし（デフォルト）", 
        "あり（通常）", 
        "あり＋キラキラ（B以上濃厚）", 
        "Vロゴ（天国濃厚）"
    ])

    # --- 画像データに基づく「天井周期」と「天井G数」の自動セット ---
    # 天井周期の決定
    if m_helmet == "Vロゴ（天国濃厚）":
        d_target_cycle = 1
    elif m_helmet == "あり＋キラキラ（B以上濃厚）":
        d_target_cycle = 3
    elif "リセット" in m_condition:
        d_target_cycle = 4
    else:
        d_target_cycle = 6

    # 天井G数の決定（短縮契機以外は一律795G）
    if "リセット" in m_condition:
        d_target_g = 495
    else:
        d_target_g = 795

with m_col2:
    m_rival_full = st.selectbox("状態・ライバル", [
        "なし", 
        "榎木 (優出モード期待度50％以上)", 
        "洞口 (シナリオ ギャンブラー以上)", 
        "蒲生 (強チェで超抜チャレンジ濃厚)", 
        "浜岡 (規定激走最大222pt)", 
        "青島 (青島SG濃厚)", 
        "モノクロ波多野 (最強のB2 or 艇王)",
    ])
    
    # 浜岡選択時
    if "浜岡" in m_rival_full:
        d_c1_pt, d_c6_pt, d_normal_pt = 222, 222, 222
        
    # --- TY（期待獲得枚数）の計算 ---
    base_ty = 194
    if "モノクロ" in m_rival_full:
        st.warning("⚠️ モノクロ波多野：最強のB2(1戦目2%) or 艇王")
        d_exp_out = 1022
    elif "青島" in m_rival_full:
        d_exp_out = 1000
    elif "洞口" in m_rival_full:
        d_exp_out = base_ty + 129
    else:
        d_exp_out = base_ty

# --- 5. メイン入力 ---
st.subheader("📍 現在の状況入力")
col1, col2 = st.columns(2)
with col1:
    current_g = st.number_input("現在のハマりG数", value=0, min_value=0)
    target_g = st.number_input("適用天井G数", value=int(d_target_g))
with col2:
    current_cycle = st.number_input("現在の周期", value=1, min_value=1)
    target_cycle = st.number_input("天井周期", value=int(d_target_cycle))

st.divider()
col3, col4 = st.columns(2)
with col3:
    total_current_g = st.number_input("AT間（累計）現在G", value=0)
    total_target_g = st.number_input("AT間（累計）天井G", value=0)
with col4:
    current_pt = st.number_input("現在の保有周期pt", value=0)
    if current_cycle == 1:
        target_pt = st.number_input("1周期目の天井pt", value=int(d_c1_pt))
    elif current_cycle == target_cycle:
        target_pt = st.number_input("天井周期の天井pt", value=int(d_c6_pt))
    else:
        target_pt = st.number_input("通常周期の天井pt", value=int(d_normal_pt))

st.divider()
final_base = st.number_input("50枚あたりの回転数(G)", value=float(d_base), step=0.1)
final_exp_out = st.number_input("期待獲得枚数(TY)", value=int(d_exp_out), step=5)

# --- 6. 計算ロジック（モンキー専用） ---

def calculate_profit(target_ty):
    """指定されたTYで収支を計算する内部関数"""
    limit_rem_g = max(1, target_g - current_g)
    
    base_prob = 1 / conf_hit
    if limit_rem_g > 600: effective_prob = base_prob * 0.9
    elif limit_rem_g > 400: effective_prob = base_prob * 1.1
    elif limit_rem_g > 200: effective_prob = base_prob * 1.5
    elif limit_rem_g > 100: effective_prob = base_prob * 2.5
    else: effective_prob = base_prob * 5.0

    p = effective_prob
    n = limit_rem_g
    avg_rem_g = (1/p) * (1 - math.pow(1 - p, n)) if p > 0 else n

    # 1. ライバルによる短縮
    if "榎木" in m_rival_full: avg_rem_g *= 0.8
    elif "蒲生" in m_rival_full: avg_rem_g *= 0.85
    
    # 2. 現在の周期による短縮
    cycle_bonus = (current_cycle - 1) / target_cycle * 0.5
    avg_rem_g *= (1 - cycle_bonus)
    
    # 3. 現在のptによる短縮
    pt_factor = current_pt / target_pt if target_pt > 0 else 0
    avg_rem_g *= (1 - (pt_factor * 0.35))

    internal_avg_g = avg_rem_g + 32 
    inv_mai = internal_avg_g * (50 / final_base)
    inv_yen = (inv_mai / kashidashi_mai) * 1000
    out_yen = target_ty * (100 / koukan_rate)
    
    return out_yen - inv_yen, limit_rem_g, internal_avg_g

# 2パターンの期待値を算出
profit_real, rem_g, avg_g = calculate_profit(final_exp_out)
profit_public, _, _ = calculate_profit(final_exp_out + 244)

# --- 7. 結果表示 ---
st.divider()

col_res_a, col_res_b = st.columns(2)

with col_res_a:
    st.subheader("🛠️ 職人の辛口評価")
    if profit_real >= 0:
        st.success(f"期待収支: ＋{math.floor(profit_real):,} 円")
    else:
        st.error(f"期待収支: {math.floor(profit_real):,} 円")
    st.caption(f"TY {final_exp_out}枚（実力値ベース）")

with col_res_b:
    st.subheader("📢 世間の公表値ベース")
    if profit_public >= 0:
        st.success(f"期待収支: ＋{math.floor(profit_public):,} 円")
    else:
        st.error(f"期待収支: {math.floor(profit_public):,} 円")
    st.caption(f"TY {final_exp_out + 244}枚（公表値バフ込）")

st.divider()
m1, m2, m3 = st.columns(3)
with m1: st.metric("天井まで残り", f"{rem_g} G")
with m2: st.metric("平均投資枚数", f"{math.ceil(avg_g * (50/final_base))} 枚")
with m3: st.metric("最大投資額", f"{math.ceil(math.ceil((rem_g+32)*(50/final_base))/kashidashi_mai)*1000:,} 円")
