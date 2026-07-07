"""設定・CSVインポート・エクスポートページ"""
import streamlit as st
import pandas as pd

from modules.csv_handler import (
    import_from_csv, export_to_csv, get_import_template_csv
)
from modules.database import (
    get_payments_df, bulk_insert_payments, get_all_payments_df
)
from utils.helpers import get_current_year_month, format_currency
from config.settings import APP_NAME, APP_VERSION


def show_settings():
    user_id = st.session_state["user_id"]

    st.markdown("## ⚙️ 設定・インポート・エクスポート")

    tab1, tab2, tab3, tab4 = st.tabs([
        "☁️ Supabase",
        "📥 CSVインポート",
        "📤 CSVエクスポート",
        "ℹ️ システム情報",
    ])

    # ─── Tab1: Supabase 情報 ──────────────────────────────

    with tab1:
        st.markdown("### ☁️ Supabase データベース")
        st.info(
            "データは Supabase のクラウドデータベースに保存されています。  \n"
            "アプリのスリープ・再起動によるデータ消失はありません。"
        )

        try:
            from modules.supabase_client import get_supabase
            get_supabase()
            st.success("✅ Supabase に接続中")
        except Exception as e:
            st.error(f"❌ Supabase 接続エラー: {e}")

        st.divider()
        st.markdown("#### バックアップについて")
        st.markdown(
            "データのバックアップは **Supabase ダッシュボード** から管理できます。  \n"
            "- **Settings → Database → Backups** でポイントインタイムリカバリが利用可能です。  \n"
            "- CSV エクスポート（📤 CSVエクスポートタブ）でローカルにデータを保存できます。"
        )

        st.divider()
        st.markdown("#### 接続設定")
        st.code(
            "# .streamlit/secrets.toml\n"
            'SUPABASE_URL = "https://your-project.supabase.co"\n'
            'SUPABASE_ANON_KEY = "your-anon-key"',
            language="toml",
        )

    # ─── Tab2: CSVインポート ──────────────────────────────

    with tab2:
        st.markdown("### 📥 CSVインポート")

        year, month = get_current_year_month()
        col_y, col_m = st.columns(2)
        with col_y:
            import_year = st.selectbox(
                "取込先 年", range(2020, 2031),
                index=list(range(2020, 2031)).index(year),
            )
        with col_m:
            import_month = st.selectbox(
                "取込先 月", range(1, 13),
                index=month - 1,
                format_func=lambda m: f"{m}月",
            )

        st.markdown("#### テンプレートダウンロード")
        template_csv = get_import_template_csv()
        st.download_button(
            "📄 CSVテンプレートをダウンロード",
            data=template_csv.encode("utf-8-sig"),
            file_name="支払い管理_インポートテンプレート.csv",
            mime="text/csv",
        )

        st.markdown("#### CSVファイルをアップロード")
        st.caption("列名：支払先、支払内容、固定変動（固定/変動）、支払日（日）、金額、支払方法、カテゴリ、備考")

        uploaded = st.file_uploader(
            "CSVファイルを選択", type=["csv"],
            help="UTF-8またはShift-JIS形式のCSVファイルに対応しています",
        )

        if uploaded:
            try:
                with st.spinner("CSVを解析中..."):
                    payments, warnings = import_from_csv(uploaded.read(), import_year, import_month)
            except ValueError as e:
                st.error(f"❌ エラー：{e}")
                return

            if warnings:
                with st.expander(f"⚠️ 警告 {len(warnings)} 件", expanded=True):
                    for w in warnings:
                        st.warning(w)

            if payments:
                st.success(f"✅ {len(payments)} 件のデータを読み込みました。")
                preview_df = pd.DataFrame(payments)[
                    ["payee", "description", "payment_type", "payment_day",
                     "amount", "payment_method", "category", "adjusted_date"]
                ].copy()
                preview_df.columns = ["支払先", "支払内容", "固定変動", "支払日",
                                       "金額", "支払方法", "カテゴリ", "調整後支払日"]
                st.dataframe(preview_df, use_container_width=True, height=250)

                if st.button(
                    f"▶ {import_year}年{import_month}月にインポートする",
                    type="primary",
                ):
                    for p in payments:
                        p["user_id"] = user_id
                    with st.spinner("インポート中..."):
                        count = bulk_insert_payments(payments)
                    st.success(f"✅ {count} 件をインポートしました！")
                    st.session_state["view_year"]  = import_year
                    st.session_state["view_month"] = import_month
                    st.balloons()
            else:
                st.warning("インポートできるデータが見つかりませんでした。")

    # ─── Tab3: CSVエクスポート ────────────────────────────

    with tab3:
        st.markdown("### 📤 CSVエクスポート")

        year, month = get_current_year_month()
        col_ey, col_em = st.columns(2)
        with col_ey:
            exp_year = st.selectbox(
                "出力 年", range(2020, 2031),
                index=list(range(2020, 2031)).index(year),
                key="exp_year",
            )
        with col_em:
            exp_month = st.selectbox(
                "出力 月", range(1, 13),
                index=month - 1,
                format_func=lambda m: f"{m}月",
                key="exp_month",
            )

        df_exp = get_payments_df(exp_year, exp_month, user_id)
        if not df_exp.empty:
            st.info(
                f"{exp_year}年{exp_month}月：{len(df_exp)} 件　"
                f"合計 {format_currency(df_exp['amount'].sum())}"
            )
            csv_data = export_to_csv(df_exp)
            st.download_button(
                f"📄 {exp_year}年{exp_month}月をCSV出力",
                data=csv_data.encode("utf-8-sig"),
                file_name=f"支払い管理_{exp_year}年{exp_month}月.csv",
                mime="text/csv",
                type="primary",
            )
        else:
            st.info("選択した月にはデータがありません。")

        st.divider()
        st.markdown("#### 年間データ一括出力")
        df_all = get_all_payments_df(exp_year, user_id)
        if not df_all.empty:
            csv_all = export_to_csv(df_all)
            st.download_button(
                f"📄 {exp_year}年 全データをCSV出力",
                data=csv_all.encode("utf-8-sig"),
                file_name=f"支払い管理_{exp_year}年_全データ.csv",
                mime="text/csv",
            )

    # ─── Tab4: システム情報 ───────────────────────────────

    with tab4:
        st.markdown("### ℹ️ システム情報")

        import os
        supabase_url = ""
        try:
            import streamlit as _st
            supabase_url = _st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "（未設定）")
        except Exception:
            supabase_url = os.environ.get("SUPABASE_URL", "（未設定）")

        info_rows = [
            ("アプリ名",             APP_NAME),
            ("バージョン",           APP_VERSION),
            ("Streamlit バージョン", st.__version__),
            ("データベース",         "Supabase (PostgreSQL)"),
            ("Supabase URL",         supabase_url),
            ("ログインユーザー",     st.session_state.get("user_name", "")),
            ("メールアドレス",       st.session_state.get("user_email", "")),
        ]

        for label, value in info_rows:
            c1, c2 = st.columns([2, 4])
            c1.markdown(f"**{label}**")
            c2.code(value, language=None)

        st.divider()
        st.markdown("#### 拡張予定の機能（ロードマップ）")
        st.markdown("""
        - 🤖 **AI分析**：支出パターン分析・異常検知
        - 📅 **Googleカレンダー連携**：支払日を自動登録
        - 📱 **LINE通知**：支払い期限をLINEで通知
        - 📧 **メール通知**：期限超過時の自動メール
        - 📊 **予算管理機能**：カテゴリ別予算設定と差異分析
        """)
