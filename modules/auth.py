"""Supabase Auth を使ったユーザー認証"""
from modules.supabase_client import get_supabase


def register_user(name: str, email: str, password: str) -> tuple[bool, str]:
    if not name.strip():
        return False, "名前を入力してください"
    if len(password) < 8:
        return False, "パスワードは8文字以上で入力してください"

    client = get_supabase()
    try:
        response = client.auth.sign_up({
            "email": email.strip(),
            "password": password,
            "options": {"data": {"name": name.strip()}},
        })
        if response.user:
            if response.session is None:
                return True, "確認メールを送信しました。メールのリンクをクリックしてからログインしてください。"
            return True, "登録が完了しました"
        return False, "登録に失敗しました"
    except Exception as e:
        msg = str(e)
        if "already registered" in msg or "already exists" in msg or "User already registered" in msg:
            return False, "このメールアドレスはすでに登録されています"
        return False, f"登録エラー: {msg}"


def login_user(email: str, password: str) -> tuple[bool, dict | None, str]:
    if not email.strip() or not password:
        return False, None, "メールアドレスとパスワードを入力してください"

    client = get_supabase()
    try:
        response = client.auth.sign_in_with_password({
            "email": email.strip(),
            "password": password,
        })
        if response.session and response.user:
            user = response.user
            session = response.session
            name = (user.user_metadata or {}).get("name", email.split("@")[0])
            return True, {
                "id":            user.id,
                "name":          name,
                "email":         user.email,
                "access_token":  session.access_token,
                "refresh_token": session.refresh_token,
            }, "ログインしました"
        return False, None, "ログインに失敗しました"
    except Exception as e:
        msg = str(e)
        if "Email not confirmed" in msg:
            return False, None, "メールアドレスの確認が完了していません。確認メールのリンクをクリックしてください。"
        if "Invalid login credentials" in msg or "invalid_credentials" in msg:
            return False, None, "メールアドレスまたはパスワードが正しくありません"
        return False, None, f"ログインエラー: {msg}"
