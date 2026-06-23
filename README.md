# 削減アミダクジ — 運営ツール（GitHub Pages デプロイ用）

リアル交渉ゲーム「削減アミダクジ」の運営ツール一式。

- **集計ツール** (`tool.html`): ディーラー用。セッション管理／場所決め投票／本戦集計／最終結果
- **発表ツール** (`present.html`): プレイヤー卓のスクリーン用。ルール説明／タイマー／結果発表
- **ランディング** (`index.html`): 上記2ツールへのリンク

データストアは Supabase（`wiqnmebudaadwqdaxwko`）を共有しているため、両ツールは同じセッションを参照します。

---

## 🚀 セットアップ（GitHub Pages）

### 1. リポジトリ作成

GitHub で新規 public リポジトリを作成（例: `amida-tools`）。

### 2. ファイル一式をプッシュ

このフォルダの全ファイル（`index.html` / `tool.html` / `present.html` / `CNAME` / `README.md`）をリポジトリ直下に配置してプッシュ：

```bash
cd /path/to/this/folder
git init
git add .
git commit -m "initial deploy"
git branch -M main
git remote add origin git@github.com:<your-account>/amida-tools.git
git push -u origin main
```

### 3. GitHub Pages 有効化

リポジトリの **Settings → Pages**：
- **Source**: `Deploy from a branch`
- **Branch**: `main` / `(root)`
- 保存

数十秒〜数分で `https://<your-account>.github.io/amida-tools/` で公開されます。

### 4. カスタムドメイン `amida.puzzliar.jp`（任意）

リポジトリには既に `CNAME` ファイル（中身 = `amida.puzzliar.jp`）が含まれています。

#### DNS 設定（puzzliar.jp の DNS 管理画面で）

`amida` サブドメインを GitHub Pages の IP / CNAME に向ける：

**Option A: CNAME レコード（推奨）**
```
amida.puzzliar.jp.   CNAME   <your-account>.github.io.
```

**Option B: A レコード（ apex ドメインも使いたい場合）**
```
amida.puzzliar.jp.   A   185.199.108.153
amida.puzzliar.jp.   A   185.199.109.153
amida.puzzliar.jp.   A   185.199.110.153
amida.puzzliar.jp.   A   185.199.111.153
```

DNS 反映後、GitHub Settings → Pages で「Custom domain」に `amida.puzzliar.jp` を入力。「Enforce HTTPS」を有効化（Let's Encrypt 証明書が自動発行）。

### 5. アクセス確認

- ランディング: https://amida.puzzliar.jp/
- 集計ツール: https://amida.puzzliar.jp/tool.html
- 発表ツール: https://amida.puzzliar.jp/present.html

---

## 🔧 更新（バージョンアップ時）

新版を入手したら、リポジトリの `tool.html` / `present.html` を差し替えてコミット → プッシュ。  
数分以内に GitHub Pages が再ビルドされ自動反映されます。

```bash
# 例
cp ~/Downloads/amida_tool_v6.4.html tool.html
cp ~/Downloads/amida_present_v6.4.html present.html
git add tool.html present.html
git commit -m "update to v6.4"
git push
```

---

## ⚠️ 重要事項

### Supabase Anon Key の公開について

両 HTML には Supabase の Anon Key が埋め込まれています。Anon Key は public とすることを前提とした鍵で、データベース側の Row Level Security (RLS) で守られています。リポジトリを public にしても Anon Key の漏洩はセキュリティ上の問題になりません。

ただし、`amida_sessions` テーブルが現状 RLS 未設定で全アクセス可能の場合、Supabase Dashboard で適切な RLS ポリシーを設定することを推奨します。

### Supabase プロジェクトの状態

無料プランは1週間以上 inactive で自動 pause されます。長期間使わない予定がある場合は Supabase Dashboard で定期的にアクセス／プロジェクトを restore してください。

---

## 📂 ファイル構成

```
amida-tools/
├─ index.html       # ランディングページ
├─ tool.html        # 集計ツール (v6.3)
├─ present.html     # 発表ツール (v6.3)
├─ CNAME            # GitHub Pages 用カスタムドメイン定義
└─ README.md        # このファイル
```

---

最終更新: 2026-06-23
