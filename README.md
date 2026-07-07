# 💳 支払い管理システム Ver.2.0

毎月の固定費・変動費を一元管理する業務用 Web アプリです。  
Python / Streamlit 製。データベースに **Supabase (PostgreSQL)** を使用し、クラウドに永続保存します。

---

## 主な機能

| 機能 | 詳細 |
|------|------|
| ユーザー認証 | メールアドレス + パスワードでログイン。Supabase Auth 利用 |
| マルチユーザー対応 | ユーザーごとにデータが完全分離 |
| 支払い登録・編集・削除 | 固定（金額固定）/ 固定（金額変動）/ 変動 の 3 種別 |
| 翌月繰り越し | 固定支払いをワンクリックで翌月へコピー。金額変動は繰り越し時に金額入力 |
| 祝日・土日自動調整 | 支払日が土日・祝日の場合、翌営業日に自動調整 |
| ダッシュボード | KPI 8 項目 + 円グラフ + 月別棒グラフ + 今週の支払い予定 + 期限超過アラート |
| Excel 出力（7 シート） | 支払い一覧 / 月別一覧 / 支払先一覧 / 集計 / 月別集計 / 年間集計 / カテゴリ別集計 |
| CSV インポート / エクスポート | テンプレート付き。Shift-JIS / UTF-8 両対応 |
| ステータス管理 | 未払い / 支払済み / 期限超過 / 期限間近 を色分け表示 |

---

## 動作環境

- **Python 3.10 以上**（推奨: 3.13）
- Windows / macOS / Linux
- ブラウザ（Chrome / Edge / Firefox 推奨）

---

## Supabase セットアップ

アプリを使用するには、Supabase プロジェクトの作成と設定が必要です。

### 1. Supabase プロジェクトを作成

1. [supabase.com](https://supabase.com) にアクセスしてアカウントを作成
2. **「New project」** をクリックしてプロジェクトを作成
3. プロジェクト名・データベースパスワードを設定

### 2. データベーステーブルを作成

Supabase ダッシュボード → **「SQL Editor」** を開き、`supabase/schema.sql` の内容を貼り付けて **「Run」** をクリックします。

```sql
-- supabase/schema.sql の内容を実行してください
```

### 3. メール確認を無効化（推奨）

開発・テスト時は登録後すぐにログインできるよう、メール確認を無効にすることを推奨します。

Supabase ダッシュボード → **Authentication → Settings → Email** →  
**「Enable email confirmations」** を OFF にする

### 4. Supabase の接続情報を取得

Supabase ダッシュボード → **Settings → API** から以下をコピーします：

| 項目 | 場所 |
|------|------|
| `SUPABASE_URL` | Project URL |
| `SUPABASE_ANON_KEY` | Project API Keys → `anon public` |

---

## ローカルでのセットアップ手順

### 1. リポジトリをクローン

```bash
git clone https://github.com/ss000811/payment-manager.git
cd payment-manager
```

### 2. 仮想環境を作成（推奨）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. Supabase の接続情報を設定

`.streamlit/secrets.toml` ファイルを編集します（テンプレートあり）：

```toml
# .streamlit/secrets.toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
```

> このファイルは `.gitignore` により Git 管理対象外です。絶対に公開しないでください。

### 5. アプリを起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動で開きます。

> **Windows の場合** `start.bat` をダブルクリックするだけで起動できます。

---

## Streamlit Community Cloud へのデプロイ

### 初回デプロイ手順

1. [share.streamlit.io](https://share.streamlit.io) にアクセスし、GitHub アカウントでログイン
2. **「New app」** をクリック
3. 以下の設定を入力：

   | 項目 | 設定値 |
   |------|--------|
   | Repository | `ss000811/payment-manager` |
   | Branch | `main` |
   | Main file path | `app.py` |

4. **「Advanced settings」→「Secrets」** に以下を貼り付ける：

```toml
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
```

5. **「Deploy!」** をクリック → 数分でデプロイ完了

### データの永続化について

Supabase を使用しているため、Streamlit Cloud のスリープ後もデータは保持されます。

| 環境 | データ永続化 |
|------|-------------|
| ローカル | ✅ Supabase クラウドに永続保存 |
| Streamlit Cloud | ✅ Supabase クラウドに永続保存 |

---

## デプロイ後のアプリ更新方法

コードを修正して GitHub に Push すると、**Streamlit Cloud が自動的に再デプロイ**します。

```bash
git add .
git commit -m "fix: 修正内容を説明するメッセージ"
git push origin main
```

> Push から反映まで通常 **1〜2 分**かかります。

---

## フォルダ構成

```
payment-manager/
├── app.py                      # メインエントリポイント
├── requirements.txt            # 依存パッケージ
├── start.bat                   # Windows用 ワンクリック起動スクリプト
│
├── supabase/
│   └── schema.sql              # Supabase テーブル定義 SQL
│
├── .streamlit/
│   ├── config.toml             # Streamlit テーマ・サーバー設定
│   └── secrets.toml            # Supabase 接続情報（git 管理外）
│
├── config/
│   └── settings.py             # 定数・マスターデータ
│
├── modules/
│   ├── supabase_client.py      # Supabase クライアントファクトリ
│   ├── auth.py                 # Supabase Auth（ログイン・登録）
│   ├── database.py             # Supabase CRUD・集計クエリ
│   ├── holiday.py              # 祝日判定・翌営業日計算
│   ├── excel_export.py         # Excel 7シート出力
│   └── csv_handler.py          # CSV インポート / エクスポート
│
├── views/
│   ├── login.py                # ログイン・新規登録画面
│   ├── dashboard.py            # ダッシュボード画面
│   ├── payment_list.py         # 支払い管理画面（メイン操作）
│   └── settings_page.py        # 設定・インポート・エクスポート画面
│
├── utils/
│   ├── helpers.py              # 共通ユーティリティ関数
│   └── validators.py           # 入力バリデーション
│
└── assets/
    └── style.css               # カスタム CSS
```

---

## 使い方

### アカウントを作成する

1. アプリを開くと「🔑 ログイン」「📝 新規登録」タブが表示されます
2. **「📝 新規登録」** タブでお名前・メールアドレス・パスワードを入力して登録

### 支払いを登録する

1. サイドバーから **「📋 支払い管理」** を選択
2. **「➕ 支払いを追加」** ボタンをクリック
3. 支払先・金額・支払日などを入力して **「登録する」**

### 翌月へ繰り越す

1. 当月の支払い管理画面で **「📅 翌月へ繰り越し」** をクリック
2. 繰り越したい項目にチェック（デフォルト全選択）
3. **「固定（金額変動）」** の項目は翌月の金額を入力
4. **「▶ 登録する」** で完了

### Excel をダウンロードする

1. 支払い管理画面で **「📊 Excel 出力」** をクリック
2. 7 シート構成の Excel ファイルがダウンロードされます

---

## 依存ライブラリ

| ライブラリ | 用途 |
|------------|------|
| streamlit | Web UI フレームワーク |
| supabase | Supabase クライアント（Auth + DB） |
| pandas | データ処理 |
| openpyxl | Excel ファイル生成 |
| jpholiday | 日本の祝日判定 |
| plotly | グラフ描画 |

---

## ライセンス

MIT License
