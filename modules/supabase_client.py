"""Supabase クライアントのファクトリ"""
import os
import streamlit as st
from supabase import create_client, Client


def _get_credentials() -> tuple[str, str]:
    try:
        url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_ANON_KEY", "")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL と SUPABASE_ANON_KEY が設定されていません。\n"
            ".streamlit/secrets.toml または環境変数を確認してください。"
        )
    return url, key


def get_supabase() -> Client:
    """
    認証セッション付きの Supabase クライアントを返す。
    session_state に access_token があれば自動でセッションを復元する。
    """
    url, key = _get_credentials()
    client = create_client(url, key)

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            for k in ["user_id", "user_name", "user_email", "access_token", "refresh_token"]:
                st.session_state.pop(k, None)

    return client
