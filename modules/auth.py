"""ユーザー認証モジュール"""
import hashlib
import os
from datetime import datetime

from modules.database import get_connection


def hash_password(password: str) -> str:
    """パスワードをソルト付き PBKDF2-SHA256 ハッシュに変換"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, password_hash: str) -> bool:
    """平文パスワードとハッシュを照合する"""
    try:
        salt_hex, key_hex = password_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return key.hex() == key_hex
    except Exception:
        return False


def register_user(name: str, email: str, password: str) -> tuple[bool, str]:
    """
    新規ユーザーを登録する。
    Returns: (success, message)
    """
    name = name.strip()
    email = email.strip().lower()

    if not name:
        return False, "名前を入力してください"
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return False, "有効なメールアドレスを入力してください"
    if len(password) < 8:
        return False, "パスワードは8文字以上で入力してください"

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            return False, "このメールアドレスはすでに登録されています"

        conn.execute(
            """
            INSERT INTO users (name, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, hash_password(password), datetime.now().isoformat()),
        )
    return True, "登録が完了しました"


def login_user(email: str, password: str) -> tuple[bool, dict | None, str]:
    """
    メール・パスワードで認証する。
    Returns: (success, user_dict, message)
    """
    email = email.strip().lower()

    if not email or not password:
        return False, None, "メールアドレスとパスワードを入力してください"

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not row:
        return False, None, "メールアドレスまたはパスワードが正しくありません"

    user = dict(row)
    if not verify_password(password, user["password_hash"]):
        return False, None, "メールアドレスまたはパスワードが正しくありません"

    return True, {"id": user["id"], "name": user["name"], "email": user["email"]}, "ログインしました"
