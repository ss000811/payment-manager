"""ダッシュボードページ"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date, timedelta

from modules.database import get_dashboard_stats, get_payments_df, get_monthly_summary
from utils.helpers import format_currency, get_current_year_month, get_effective_status, status_label


def show_dashboard():
    user_id = st.session_state["user_id"]
    year, month = st.session_state.get("view_year"), st.session_state.get("view_month")
    if not year or not month:
        year, month = get_current_year_month()

    st.markdown(f"## 📊 ダッシュボード　{year}年{month}月")

    with st.spinner("データを読み込み中..."):
        stats = get_dashboard_stats(year, month, user_id)
        df = get_payments_df(year, month, user_id)

    # ─── KPIカード（2行×4列）───────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("今月 支払件数", f"{stats['total_count']} 件",
                  help="今月登録されている支払い件数")
    with c2:
        st.metric("今月 支払総額", format_currency(stats["total_amount"]),
                  help="今月の支払い合計金額")
    with c3:
        st.metric("支払済み", f"{stats['paid_count']} 件",
                  f"{format_currency(stats['paid_amount'])}",
                  help="支払済みの件数と金額")
    with c4:
        st.metric("未払い", f"{stats['unpaid_count']} 件",
                  f"{format_currency(stats['unpaid_amount'])}",
                  delta_color="inverse", help="未払いの件数と金額")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("🔴 期限超過", f"{stats['overdue_count']} 件",
                  delta_color="inverse", help="支払日を過ぎた未払い件数")
    with c6:
        st.metric("📅 今週 支払い予定", f"{stats['this_week_count']} 件",
                  help="本日から7日以内に支払日が来る件数")
    with c7:
        st.metric("🔒 固定支払い", f"{stats['fixed_count']} 件",
                  help="今月の固定支払い件数")
    with c8:
        st.metric("🔄 変動支払い", f"{stats['variable_count']} 件",
                  help="今月の変動支払い件数")

    st.divider()

    # ─── チャート ──────────────────────────────────────────
    col_chart1, col_chart2 = st.columns([1, 2])

    with col_chart1:
        st.markdown("#### 支払い状況")
        if stats["total_count"] > 0:
            paid    = stats["paid_count"]
            overdue = stats["overdue_count"]
            unpaid  = max(0, stats["unpaid_count"] - overdue)
            fig = go.Figure(data=[go.Pie(
                labels=["支払済み", "未払い", "期限超過"],
                values=[paid, unpaid, overdue],
                hole=0.45,
                marker_colors=["#4CAF50", "#2196F3", "#F44336"],
                textinfo="label+percent",
                textfont_size=11,
            )])
            fig.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("データがありません")

    with col_chart2:
        st.markdown("#### 月別支払い推移")
        monthly = get_monthly_summary(year, user_id)
        if not monthly.empty:
            months_all = pd.DataFrame({"month": range(1, 13)})
            monthly = months_all.merge(monthly, on="month", how="left").fillna(0)
            monthly["month_label"] = monthly["month"].apply(lambda m: f"{int(m)}月")
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=monthly["month_label"], y=monthly["total"],
                name="支払総額", marker_color="#2196F3", opacity=0.8,
            ))
            fig2.add_trace(go.Bar(
                x=monthly["month_label"], y=monthly["paid"],
                name="支払済み", marker_color="#4CAF50", opacity=0.9,
            ))
            fig2.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                barmode="overlay",
                legend=dict(orientation="h", y=1.1),
                yaxis=dict(tickformat=",.0f"),
                xaxis_title=None,
                yaxis_title="金額（円）",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("月別データがありません")

    st.divider()

    # ─── 今週の支払い予定 ──────────────────────────────────
    st.markdown("#### 📅 今週の支払い予定")
    today    = date.today()
    week_end = today + timedelta(days=6)

    if not df.empty:
        df["eff_status"] = df.apply(
            lambda r: get_effective_status(r["status"], r.get("adjusted_date", "")), axis=1
        )
        week_df = df[
            (df["adjusted_date"] >= today.isoformat()) &
            (df["adjusted_date"] <= week_end.isoformat()) &
            (df["status"] != "paid")
        ].copy()

        if not week_df.empty:
            week_df["支払日"] = week_df["adjusted_date"]
            week_df["支払先"] = week_df["payee"]
            week_df["内容"]   = week_df["description"]
            week_df["金額"]   = week_df["amount"].apply(format_currency)
            week_df["方法"]   = week_df["payment_method"]
            week_df["状態"]   = week_df["eff_status"].apply(status_label)
            display = week_df[["支払日", "支払先", "内容", "金額", "方法", "状態"]].reset_index(drop=True)
            st.dataframe(display, use_container_width=True, height=min(200, 38 * len(display) + 38))
        else:
            st.success("今週の支払い予定はありません ✅")
    else:
        st.info("今月のデータがありません。支払い管理ページから登録してください。")

    # ─── 期限超過アラート ───────────────────────────────────
    if stats["overdue_count"] > 0:
        st.divider()
        st.markdown("#### 🔴 期限超過の支払い")
        if not df.empty:
            today_str  = date.today().isoformat()
            overdue_df = df[(df["status"] == "unpaid") & (df["adjusted_date"] < today_str)].copy()
            if not overdue_df.empty:
                overdue_df["支払日"]   = overdue_df["adjusted_date"]
                overdue_df["支払先"]   = overdue_df["payee"]
                overdue_df["内容"]     = overdue_df["description"]
                overdue_df["金額"]     = overdue_df["amount"].apply(format_currency)
                overdue_df["経過日数"] = overdue_df["adjusted_date"].apply(
                    lambda d: f"{(date.today() - date.fromisoformat(d)).days}日超過" if d else ""
                )
                display_ov = overdue_df[["支払日", "支払先", "内容", "金額", "経過日数"]].reset_index(drop=True)
                st.dataframe(
                    display_ov.style.map(lambda _: "background-color: #FFEBEE"),
                    use_container_width=True,
                    height=min(200, 38 * len(display_ov) + 38),
                )
