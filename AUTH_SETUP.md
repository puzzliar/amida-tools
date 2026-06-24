# 承認制 Google ログイン — セットアップ手順

両ツール（集計／発表）を **承認された Google アカウント** でのみ使用できるようにする設定。

- 管理者: **dai@puzzliar.jp**（初期投入済み）
- 新規ユーザーは Google でログイン → 申請 → 管理者が承認 → 利用可能

## 概要

```
┌──────────────────────────────────────────┐
│ 1. Google Cloud Console で OAuth Client 作成  │
│ 2. Supabase で Google プロバイダを有効化           │
│ 3. Supabase で SQL 実行（user_approvals テーブル）│
│ 4. ツール側 (HTML) を v7 にアップデート              │
└──────────────────────────────────────────┘
```

## ステップ 1: Google Cloud Console で OAuth Client 作成

### 1-1. プロジェクト準備
🔗 https://console.cloud.google.com/ → 既存プロジェクトを選択（なければ新規作成）

### 1-2. OAuth 同意画面の設定
左メニュー: **API とサービス → OAuth 同意画面**

- User Type: **外部** を選択 → 作成
- アプリ名: `削減アミダクジ 運営ツール`
- ユーザーサポートメール: `dai@puzzliar.jp`
- デベロッパーの連絡先: `dai@puzzliar.jp`
- 「保存して次へ」を順次クリック
- 「テストユーザー」は空のまま「保存して次へ」（公開モードに切り替える場合は後述）

### 1-3. OAuth クライアント ID 作成
左メニュー: **API とサービス → 認証情報** → 「**+ 認証情報を作成**」 → **OAuth クライアント ID**

| 項目 | 値 |
|---|---|
| アプリケーションの種類 | **ウェブアプリケーション** |
| 名前 | `削減アミダクジ` |
| 承認済みの JavaScript 生成元 | `https://amida.puzzliar.jp` |
| 承認済みのリダイレクト URI | `https://wiqnmebudaadwqdaxwko.supabase.co/auth/v1/callback` |

「作成」をクリック → **クライアント ID** と **クライアント シークレット** が表示されるのでコピー（再表示可能）。

### 1-4. アプリの公開状態
OAuth 同意画面に戻り、画面上部「**アプリを公開**」ボタンをクリック。  
（テストモードのままだと、テストユーザーに登録した Google アカウントしかログインできません）

## ステップ 2: Supabase で Google プロバイダを有効化

🔗 https://supabase.com/dashboard/project/wiqnmebudaadwqdaxwko/auth/providers

「**Google**」セクションを開き：

- **Enable Sign in with Google**: ON
- **Client ID (for OAuth)**: 上記 1-3 のクライアント ID を貼り付け
- **Client Secret (for OAuth)**: 上記 1-3 のクライアントシークレットを貼り付け
- **Skip nonce check**: OFF（デフォルト）
- 「Save」

### Site URL / Redirect URLs の確認

🔗 https://supabase.com/dashboard/project/wiqnmebudaadwqdaxwko/auth/url-configuration

- **Site URL**: `https://amida.puzzliar.jp`
- **Redirect URLs** (Additional Redirect URLs)（カンマ区切りで複数指定可）:
  ```
  https://amida.puzzliar.jp
  https://amida.puzzliar.jp/
  https://amida.puzzliar.jp/tool.html
  https://amida.puzzliar.jp/present.html
  https://puzzliar.github.io/amida-tools/
  https://puzzliar.github.io/amida-tools/tool.html
  https://puzzliar.github.io/amida-tools/present.html
  http://localhost:8000
  http://localhost:8000/tool.html
  http://localhost:8000/present.html
  ```
- 「Save」

## ステップ 3: SQL 実行（user_approvals テーブル）

🔗 https://supabase.com/dashboard/project/wiqnmebudaadwqdaxwko/sql/new

同梱の `setup_auth.sql` の中身を全文コピーして貼り付け → **Run** ボタン。

実行成功後、以下のクエリで管理者投入確認：

```sql
select email, status, is_admin from public.user_approvals;
```

期待される結果：
```
email             | status   | is_admin
dai@puzzliar.jp   | approved | true
```

## ステップ 4: 動作確認

1. `https://amida.puzzliar.jp/tool.html` を開く
2. 「Google でログイン」をクリック
3. Google アカウント選択 → 同意画面 → ツールにリダイレクト
4. dai@puzzliar.jp でログインすれば即時利用可能
5. 別の Google アカウントでログインすると「承認を申請する」ボタンが表示される
6. 申請後、dai@puzzliar.jp でログイン → 集計ツール左メニューの「ユーザー管理」から承認

## トラブルシュート

### 「This app isn't verified」と Google が警告
→ OAuth 同意画面で「アプリを公開」していない、もしくは Google の確認待ち。テストユーザーに該当 Google アカウントを追加するか、「詳細」→「<アプリ名>（安全ではないページ）に移動」で進む。

### redirect_uri_mismatch
→ ステップ 1-3 の「承認済みのリダイレクト URI」が正確に `https://wiqnmebudaadwqdaxwko.supabase.co/auth/v1/callback` になっているか確認。末尾スラッシュなし。

### ログイン後に空白画面 / 無限ループ
→ ステップ 2 の Redirect URLs が網羅されているか確認。`/` 付きと無しの両方を入れる。

### 承認しても利用できない
→ SQL `select * from user_approvals where email='対象アカウント';` で status='approved' になっているか確認。RLS のキャッシュは数秒〜数分。一度ログアウト→再ログインで反映。

## セキュリティ注記

- **Anon Key は引き続き公開ですが、RLS により承認済みユーザーしかセッション/ログを読み書きできなくなります**
- 管理者を追加する場合は SQL で `update user_approvals set is_admin=true where email='...'`
- 管理者を取り消す場合も同様
- 承認/却下は管理者ツール UI から GUI 操作可能（次バージョン）

## 更新履歴

- 2026-06-23: 初版（承認制 Google ログイン導入）
