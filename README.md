# 💳 支払い管理システム Ver.1.0

毎月の固定費・変動費を一元管理する業務用 Web アプリです。  
Python / Streamlit 製。ローカル環境で完結するため、データが外部に送信されません。

---

## 主な機能

| 機能 | 詳細 |
|------|------|
| 支払い登録・編集・削除 | 固定（金額固定）/ 固定（金額変動）/ 変動 の 3 種別 |
| 翌月繰り越し | 固定支払いをワンクリックで翌月へコピー。金額変動は繰り越し時に金額入力 |
| 祝日・土日自動調整 | 支払日が土日・祝日の場合、翌営業日に自動調整（`jpholiday` 使用） |
| ダッシュボード | KPI 8 項目 + 円グラフ + 月別棒グラフ + 今週の支払い予定 + 期限超過アラート |
| Excel 出力（7 シート） | 支払い一覧 / 月別一覧 / 支払先一覧 / 集計 / 月別集計 / 年間集計 / カテゴリ別集計 |
| CSV インポート / エクスポート | テンプレート付き。Shift-JIS / UTF-8 両対応 |
| バックアップ・復元 | ローカルの `backups/` フォルダへ SQLite をコピー保存 |
| ステータス管理 | 未払い / 支払済み / 期限超過 / 期限間近 を色分け表示 |

---

## 動作環境

- **Python 3.10 以上**（推奨: 3.13）
- Windows / macOS / Linux
- ブラウザ（Chrome / Edge / Firefox 推奨）

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

### 4. アプリを起動

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

4. **「Deploy!」** をクリック → 数分でデプロイ完了

### Secrets の設定

このアプリは外部 API を使用しないため、**Secrets の設定は不要**です。

### デプロイ時の注意点

> **重要：データの永続化について**

Streamlit Community Cloud（無料プラン）は、アプリが一定時間使われないとスリープ状態になります。  
スリープから復帰すると SQLite データベースは**初期化（空）に戻ります**。

| 環境 | データ永続化 |
|------|-------------|
| ローカル（推奨） | ✅ `data/payments.db` に永続保存 |
| Streamlit Cloud | ⚠️ アプリスリープ時にデータ消去 |

**対策：**
- Streamlit Cloud はデモ・動作確認用として利用してください
- 実際の業務データはローカル環境で管理してください
- CSV エクスポートを使えばデータをローカルに保存できます

---

## デプロイ後のアプリ更新方法

コードを修正して GitHub に Push すると、**Streamlit Cloud が自動的に再デプロイ**します。

```bash
# 1. ファイルを修正した後、変更をステージング
git add .

# 2. コミット
git commit -m "fix: 修正内容を説明するメッセージ"

# 3. GitHub に Push → 自動でクラウドに反映
git push origin main
```

> Push から反映まで通常 **1〜2 分**かかります。  
> Streamlit Cloud の管理画面（share.streamlit.io）でデプロイ状況を確認できます。

---

## フォルダ構成

```
payment-manager/
├── app.py                  # メインエントリポイント
├── requirements.txt        # 依存パッケージ
├── start.bat               # Windows用 ワンクリック起動スクリプト
│
├── .streamlit/
│   └── config.toml         # Streamlit テーマ・サーバー設定
│
├── config/
│   └── settings.py         # 定数・マスターデータ
│
├── modules/
│   ├── database.py         # SQLite CRUD・集計クエリ
│   ├── holiday.py          # 祝日判定・翌営業日計算
│   ├── excel_export.py     # Excel 7シート出力
│   ├── csv_handler.py      # CSV インポート / エクスポート
│   └── backup.py           # バックアップ・復元
│
├── pages/
│   ├── dashboard.py        # ダッシュボード画面
│   ├── payment_list.py     # 支払い管理画面（メイン操作）
│   └── settings_page.py    # 設定・バックアップ・インポート画面
│
├── utils/
│   ├── helpers.py          # 共通ユーティリティ関数
│   └── validators.py       # 入力バリデーション
│
├── assets/
│   └── style.css           # カスタム CSS
│
├── data/                   # SQLite データベース（自動生成・git 管理外）
└── backups/                # バックアップファイル（自動生成・git 管理外）
```

---

## 使い方

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

## データの保存場所

| ファイル | 場所 | 内容 |
|----------|------|------|
| データベース | `data/payments.db` | 全支払いデータ（SQLite） |
| バックアップ | `backups/` | 手動バックアップのコピー |

> これらのファイルは `.gitignore` により Git 管理対象外です。  
> 大切なデータは定期的に **「💾 バックアップ作成」** ボタンで保存してください。

---

## 依存ライブラリ

| ライブラリ | バージョン | 用途 |
|------------|-----------|------|
| streamlit | 1.51.0 | Web UI フレームワーク |
| pandas | 2.3.3 | データ処理 |
| openpyxl | 3.1.5 | Excel ファイル生成 |
| jpholiday | 1.0.3 | 日本の祝日判定 |
| plotly | 6.3.0 | グラフ描画 |

---

## ライセンス

MIT License
