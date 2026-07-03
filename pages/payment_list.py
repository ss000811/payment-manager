"""支払い一覧ページ（メイン操作画面）"""
import streamlit as st
import pandas as pd
from datetime import date

from modules.database import (
    get_payments_df, add_payment, update_payment, delete_payment,
    update_payment_status, get_all_payees,
    get_rollover_candidates, check_next_month_exists, execute_rollover,
    get_all_payments_df,
)
from modules.holiday import adjust_payment_date
from modules.excel_export import export_to_excel
from modules.csv_handler import export_to_csv
from utils.helpers import (
    format_currency, get_current_year_month,
    get_effective_status, status_label,
    next_year_month, prev_year_month,
)
from utils.validators import validate_payment_form
from config.settings import (
    PAYMENT_METHODS, PAYMENT_TYPES, CATEGORIES, STATUS_OPTIONS
)


# ─── フォームダイアログ ──────────────────────────────────────

@st.dialog("支払いを登録・編集", width="large")
def payment_dialog(mode: str, payment_data: dict | None = None):
    year = st.session_state.view_year
    month = st.session_state.view_month

    existing_payees = get_all_payees()

    with st.form("payment_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            payee = st.text_input(
                "支払先 ＊",
                value=payment_data.get("payee", "") if payment_data else "",
                placeholder="例：株式会社○○",
                help="支払先の会社名・個人名を入力"
            )
            if existing_payees:
                st.caption(f"登録済み: {' / '.join(existing_payees[:5])}" +
                          ("..." if len(existing_payees) > 5 else ""))

        with col2:
            description = st.text_input(
                "支払内容",
                value=payment_data.get("description", "") if payment_data else "",
                placeholder="例：事務所家賃 2024年1月分"
            )

        col3, col4, col5 = st.columns(3)
        with col3:
            p_type_options = list(PAYMENT_TYPES.keys())
            p_type_labels = list(PAYMENT_TYPES.values())
            current_type = payment_data.get("payment_type", "fixed") if payment_data else "fixed"
            p_type_idx = p_type_options.index(current_type) if current_type in p_type_options else 0
            payment_type = st.radio(
                "支払い種別",
                options=p_type_options,
                format_func=lambda x: PAYMENT_TYPES[x],
                index=p_type_idx,
                horizontal=False,
                help="固定（金額固定）: 毎月同額 / 固定（金額変動）: 月ごとに金額が変わる固定費 / 変動: 繰り越しなし",
            )

        with col4:
            payment_day = st.number_input(
                "支払日（日）",
                min_value=1, max_value=31,
                value=int(payment_data.get("payment_day", 25)) if payment_data else 25,
                help="毎月何日払いかを入力。土日祝は翌営業日に自動調整されます。"
            )

        with col5:
            amount = st.number_input(
                "金額（円）",
                min_value=0,
                value=int(payment_data.get("amount", 0) or 0) if payment_data else 0,
                step=1000,
                format="%d",
            )

        col6, col7 = st.columns(2)
        with col6:
            method_idx = 0
            if payment_data and payment_data.get("payment_method") in PAYMENT_METHODS:
                method_idx = PAYMENT_METHODS.index(payment_data["payment_method"])
            payment_method = st.selectbox(
                "支払方法",
                options=PAYMENT_METHODS,
                index=method_idx,
            )

        with col7:
            cat_list = [""] + CATEGORIES
            cat_idx = 0
            if payment_data and payment_data.get("category") in CATEGORIES:
                cat_idx = CATEGORIES.index(payment_data["category"]) + 1
            category = st.selectbox(
                "カテゴリ",
                options=cat_list,
                index=cat_idx,
                format_func=lambda x: x if x else "（カテゴリなし）",
            )

        status_val = "unpaid"
        if payment_data:
            status_val = payment_data.get("status", "unpaid")
        status = st.selectbox(
            "ステータス",
            options=list(STATUS_OPTIONS.keys()),
            index=list(STATUS_OPTIONS.keys()).index(status_val),
            format_func=lambda x: STATUS_OPTIONS[x],
        )

        notes = st.text_area(
            "備考",
            value=payment_data.get("notes", "") if payment_data else "",
            height=70,
            placeholder="メモや注意事項など"
        )

        # 調整日プレビュー
        try:
            adj_preview = adjust_payment_date(year, month, payment_day)
            adj_str = adj_preview.strftime("%Y年%m月%d日（%a）")
            if adj_preview.day != payment_day:
                st.info(f"📅 {payment_day}日は祝日または土日のため、調整後支払日：**{adj_str}**")
            else:
                st.caption(f"📅 調整後支払日：{adj_str}")
        except Exception:
            adj_preview = None

        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            submitted = st.form_submit_button(
                "💾 保存する" if mode == "edit" else "➕ 登録する",
                type="primary",
                use_container_width=True,
            )
        with col_btn2:
            st.form_submit_button("キャンセル", use_container_width=False)

    if submitted:
        form_data = {
            "year": year,
            "month": month,
            "payee": payee,
            "description": description,
            "payment_type": payment_type,
            "payment_day": payment_day,
            "adjusted_date": adj_preview.isoformat() if adj_preview else None,
            "amount": amount,
            "payment_method": payment_method,
            "status": status,
            "category": category,
            "notes": notes,
        }
        ok, errors = validate_payment_form(form_data)
        if not ok:
            for e in errors:
                st.error(e)
        else:
            if mode == "edit" and payment_data:
                update_payment(payment_data["id"], form_data)
                st.session_state["toast_msg"] = "✅ 支払い情報を更新しました"
            else:
                add_payment(form_data)
                st.session_state["toast_msg"] = "✅ 支払いを登録しました"
            st.session_state["refresh"] = True
            st.rerun()



@st.dialog("翌月へ繰り越し　確認・編集", width="large")
def rollover_dialog(year: int, month: int):
    ny, nm = next_year_month(year, month)

    candidates = get_rollover_candidates(year, month)

    if candidates.empty:
        st.warning("固定支払いの登録がありません。「固定（金額固定）」または「固定（金額変動）」の支払いを登録してください。")
        if st.button("閉じる", use_container_width=True):
            st.rerun()
        return

    # 翌月データの既存確認
    existing_count = check_next_month_exists(ny, nm)
    if existing_count > 0:
        st.warning(
            f"⚠️ {ny}年{nm}月にはすでに **{existing_count}件** のデータがあります。"
            "　追加で登録されます（重複に注意）。"
        )

    st.markdown(
        f"**{year}年{month}月 → {ny}年{nm}月** へ繰り越します。  \n"
        "🔒 金額固定は前月金額をコピー、🔄 金額変動は今月の金額を入力してください。"
    )
    st.divider()

    # ─ テーブルヘッダー
    hc = st.columns([0.5, 3.5, 3, 1.5, 3, 1.5])
    hc[0].markdown("**含む**")
    hc[1].markdown("**支払先**")
    hc[2].markdown("**支払内容**")
    hc[3].markdown("**種別**")
    hc[4].markdown("**金額（円）**")
    hc[5].markdown("**支払日**")
    st.divider()

    # ─ 各行を st.form の外でウィジェット展開し、値をリストに収集する
    include_vals: list[bool] = []
    amount_vals: list[float] = []
    row_data: list[dict] = []

    for i, (_, row) in enumerate(candidates.iterrows()):
        ptype = row.get("payment_type", "fixed")
        is_var_amount = (ptype == "fixed_variable")
        adj = row.get("adjusted_date", "")
        try:
            adj_disp = date.fromisoformat(adj).strftime("%m/%d") if adj else ""
        except Exception:
            adj_disp = adj

        rc = st.columns([0.5, 3.5, 3, 1.5, 3, 1.5])
        with rc[0]:
            inc = st.checkbox(
                "含む", value=True,
                key=f"ro_inc_{i}",
                label_visibility="collapsed",
            )
        with rc[1]:
            st.markdown(f"**{row.get('payee', '')}**")
        with rc[2]:
            st.caption(row.get("description", ""))
        with rc[3]:
            if is_var_amount:
                st.markdown("🔄 変動")
            else:
                st.markdown("🔒 固定")
        with rc[4]:
            if is_var_amount:
                amt = st.number_input(
                    "金額",
                    min_value=0,
                    value=int(row.get("amount", 0) or 0),
                    step=1000,
                    format="%d",
                    key=f"ro_amt_{i}",
                    label_visibility="collapsed",
                )
            else:
                st.markdown(format_currency(row.get("amount", 0)))
                amt = float(row.get("amount", 0) or 0)
        with rc[5]:
            st.caption(f"{row.get('payment_day', '')}日 ({adj_disp})")

        include_vals.append(inc)
        amount_vals.append(float(amt))
        row_data.append(dict(row))

    st.divider()

    # ─ 合計プレビュー
    preview_total = sum(
        amount_vals[i]
        for i in range(len(row_data))
        if include_vals[i]
    )
    selected_count = sum(include_vals)
    st.markdown(
        f"登録対象：**{selected_count} 件**　合計：**{format_currency(preview_total)}**"
    )

    st.divider()

    bc1, bc2 = st.columns([2, 1])
    with bc1:
        if st.button(
            f"▶ {ny}年{nm}月に {selected_count}件 を登録する",
            type="primary",
            use_container_width=True,
            disabled=(selected_count == 0),
        ):
            items = [
                {**row_data[i], "amount": amount_vals[i]}
                for i in range(len(row_data))
                if include_vals[i]
            ]
            with st.spinner("登録中..."):
                count = execute_rollover(ny, nm, items)
            st.session_state["toast_msg"] = f"✅ {count}件を{ny}年{nm}月に登録しました"
            st.session_state["view_year"] = ny
            st.session_state["view_month"] = nm
            st.session_state["refresh"] = True
            st.rerun()
    with bc2:
        if st.button("キャンセル", use_container_width=True):
            st.rerun()



# ─── メインページ ──────────────────────────────────────────────

def show_payment_list():
    # ─ セッション初期化
    st.session_state.setdefault("tbl_gen", 0)       # dataframe再レンダリング用カウンター
    st.session_state.setdefault("del_id", None)      # 削除確認中のID
    st.session_state.setdefault("del_payee", "")
    st.session_state.setdefault("del_amount", 0)

    # ─ トーストメッセージ
    if st.session_state.get("toast_msg"):
        st.toast(st.session_state.pop("toast_msg"))

    # ─ 年月セレクター
    current_year, current_month = get_current_year_month()
    view_year = st.session_state.get("view_year", current_year)
    view_month = st.session_state.get("view_month", current_month)

    top_col1, top_col2, top_col3, top_col4 = st.columns([2, 1, 1, 4])

    with top_col1:
        st.markdown(f"## 📋 {view_year}年{view_month}月　支払い管理")

    with top_col2:
        if st.button("◀ 前月", use_container_width=True):
            py, pm = prev_year_month(view_year, view_month)
            st.session_state["view_year"] = py
            st.session_state["view_month"] = pm
            st.rerun()

    with top_col3:
        if st.button("翌月 ▶", use_container_width=True):
            ny, nm = next_year_month(view_year, view_month)
            st.session_state["view_year"] = ny
            st.session_state["view_month"] = nm
            st.rerun()

    with top_col4:
        c_yr, c_mo = st.columns(2)
        with c_yr:
            new_year = st.selectbox(
                "年",
                options=list(range(2020, 2031)),
                index=list(range(2020, 2031)).index(view_year),
                label_visibility="collapsed",
            )
        with c_mo:
            new_month = st.selectbox(
                "月",
                options=list(range(1, 13)),
                index=view_month - 1,
                format_func=lambda m: f"{m}月",
                label_visibility="collapsed",
            )
        if new_year != view_year or new_month != view_month:
            st.session_state["view_year"] = new_year
            st.session_state["view_month"] = new_month
            st.rerun()

    st.divider()

    # ─ フィルター・検索バー
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 2])

    with filter_col1:
        status_filter = st.selectbox(
            "絞り込み",
            options=["all", "unpaid", "paid", "overdue", "due_soon"],
            format_func=lambda x: {
                "all": "すべて",
                "unpaid": "未払い",
                "paid": "支払済み",
                "overdue": "期限超過",
                "due_soon": "期限間近（3日以内）",
            }[x],
            label_visibility="visible",
        )

    with filter_col2:
        search = st.text_input("🔍 検索", placeholder="支払先・内容・カテゴリで絞り込み", label_visibility="visible")

    with filter_col3:
        sort_options = {
            "adjusted_date": "支払日順",
            "amount": "金額順",
            "payee": "支払先順",
            "status": "ステータス順",
        }
        sort_col = st.selectbox(
            "並び替え",
            options=list(sort_options.keys()),
            format_func=lambda x: sort_options[x],
        )

    # ─ アクションボタン行
    btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([2, 2, 2, 2, 2])

    with btn_col1:
        if st.button("➕ 支払いを追加", type="primary", use_container_width=True):
            payment_dialog("add")

    with btn_col2:
        if st.button("📅 翌月へ繰り越し", use_container_width=True):
            rollover_dialog(view_year, view_month)

    with btn_col3:
        df_export = get_payments_df(view_year, view_month)
        df_year_export = get_all_payments_df(view_year)
        if not df_export.empty:
            excel_bytes = export_to_excel(df_export, df_year_export, view_year, view_month)
            st.download_button(
                "📊 Excel出力",
                data=excel_bytes,
                file_name=f"支払い管理_{view_year}年{view_month}月.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.button("📊 Excel出力", disabled=True, use_container_width=True)

    with btn_col4:
        if not df_export.empty:
            csv_str = export_to_csv(df_export)
            st.download_button(
                "📄 CSV出力",
                data=csv_str.encode("utf-8-sig"),
                file_name=f"支払い管理_{view_year}年{view_month}月.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.button("📄 CSV出力", disabled=True, use_container_width=True)

    with btn_col5:
        if st.button("🔄 更新", use_container_width=True):
            st.rerun()

    st.divider()

    # ─ データ取得
    with st.spinner("データを読み込み中..."):
        df = get_payments_df(
            view_year, view_month,
            status_filter=status_filter,
            search=search,
            sort_col=sort_col,
            sort_asc=True,
        )

    if df.empty:
        if search or status_filter != "all":
            st.info("条件に一致する支払いデータがありません。")
        else:
            st.info("この月の支払いデータはありません。「支払いを追加」から登録してください。")
        return

    # ─ サマリーバー
    total_amount = df["amount"].sum()
    paid_amount = df[df["status"] == "paid"]["amount"].sum()
    unpaid_amount = total_amount - paid_amount
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("件数", f"{len(df)} 件")
    s2.metric("合計", format_currency(total_amount))
    s3.metric("支払済み", format_currency(paid_amount))
    s4.metric("未払い", format_currency(unpaid_amount))

    st.divider()

    # ─ テーブル表示
    display_df = _build_display_df(df)

    event = st.dataframe(
        display_df,
        key=f"tbl_{st.session_state.tbl_gen}",
        use_container_width=True,
        height=min(600, 38 * len(display_df) + 55),
        on_select="rerun",
        selection_mode="single-row",
        hide_index=True,
    )

    selected_rows = event.selection.rows if event.selection else []
    selected_id = None
    selected_data = None
    if selected_rows:
        idx = selected_rows[0]
        if idx < len(df):
            row = df.iloc[idx]
            selected_id = int(row["id"])
            selected_data = dict(row)

    # ─ 選択行アクション
    if selected_id:
        st.divider()
        st.markdown(f"**選択中：** {selected_data.get('payee', '')}　{format_currency(selected_data.get('amount', 0))}")
        act1, act2, act3, act4 = st.columns(4)

        with act1:
            if selected_data.get("status") != "paid":
                if st.button("✅ 支払済みにする", type="primary", use_container_width=True):
                    update_payment_status(selected_id, "paid")
                    st.session_state["toast_msg"] = "✅ 支払済みにしました"
                    st.session_state["refresh"] = True
                    st.rerun()
            else:
                if st.button("↩ 未払いに戻す", use_container_width=True):
                    update_payment_status(selected_id, "unpaid")
                    st.session_state["toast_msg"] = "↩ 未払いに戻しました"
                    st.session_state["refresh"] = True
                    st.rerun()

        with act2:
            if st.button("✏️ 編集", use_container_width=True):
                payment_dialog("edit", selected_data)

        with act3:
            if st.button("🗑️ 削除", use_container_width=True):
                st.session_state["del_id"] = selected_id
                st.session_state["del_payee"] = selected_data.get("payee", "")
                st.session_state["del_amount"] = selected_data.get("amount", 0)
                st.rerun()

        with act4:
            st.caption("↑ 行をクリックで選択")

    # ─ インライン削除確認（ダイアログ不使用）
    if st.session_state.get("del_id"):
        st.divider()
        st.error(
            f"🗑️ **削除の確認**　「{st.session_state['del_payee']}」"
            f"（{format_currency(st.session_state['del_amount'])}）を削除します。"
            "　この操作は取り消せません。"
        )
        dc1, dc2, dc3 = st.columns([2, 2, 6])
        with dc1:
            if st.button("🗑️ 削除する", type="primary", use_container_width=True):
                delete_payment(st.session_state["del_id"])
                st.session_state["del_id"] = None
                st.session_state["tbl_gen"] += 1   # dataframeを強制再レンダリング
                st.session_state["toast_msg"] = "🗑️ 支払いを削除しました"
                st.rerun()
        with dc2:
            if st.button("キャンセル", use_container_width=True):
                st.session_state["del_id"] = None
                st.rerun()

    # ─ 凡例
    st.markdown(
        """
        <div style="font-size:12px; color:#666; margin-top:8px;">
        　凡例：
        <span style="background:#FFEBEE;padding:2px 8px;border-radius:4px;">🔴 期限超過</span>
        <span style="background:#FFF8E1;padding:2px 8px;border-radius:4px;">🟡 期限間近（3日以内）</span>
        <span style="background:#E8F5E9;padding:2px 8px;border-radius:4px;">✅ 支払済み</span>
        <span style="background:#FFFFFF;padding:2px 8px;border-radius:4px;border:1px solid #ddd;">⬜ 未払い</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """表示用DataFrameを構築（色付き）"""
    rows = []
    for _, row in df.iterrows():
        eff = get_effective_status(row.get("status", ""), row.get("adjusted_date", ""))
        adj = row.get("adjusted_date", "")
        try:
            from datetime import datetime
            adj_fmt = datetime.strptime(adj, "%Y-%m-%d").strftime("%m/%d") if adj else ""
        except Exception:
            adj_fmt = adj

        days_diff = None
        if adj:
            try:
                days_diff = (date.fromisoformat(adj) - date.today()).days
            except Exception:
                pass

        days_str = ""
        if days_diff is not None and row.get("status") != "paid":
            if days_diff < 0:
                days_str = f"({abs(days_diff)}日超過)"
            elif days_diff == 0:
                days_str = "(今日)"
            else:
                days_str = f"(あと{days_diff}日)"

        rows.append({
            "状態": status_label(eff),
            "支払先": row.get("payee", ""),
            "支払内容": row.get("description", ""),
            "固定/変動": {"fixed": "固定", "fixed_variable": "固定変動", "variable": "変動"}.get(row.get("payment_type", ""), "変動"),
            "支払日": f"{row.get('payment_day', '')}日 {adj_fmt} {days_str}".strip(),
            "金額": format_currency(row.get("amount", 0)),
            "支払方法": row.get("payment_method", ""),
            "カテゴリ": row.get("category", ""),
            "備考": row.get("notes", ""),
        })

    return pd.DataFrame(rows)


