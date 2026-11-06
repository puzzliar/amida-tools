# 削減アミダクジ プロモーション動画（Blender）

`削減アミダクジ_PV.mp4` — 1920×1080 / 30fps / 64秒 / H.264 + AAC

Blender 5.2（`bpy` モジュール、Cycles）で 3D カットを生成し、Blender の Video Sequence Editor で写真・テロップ・音声と合わせて書き出しています。

## 構成（絵コンテ）

| 時間 | カット | 素材 | テロップ |
| --- | --- | --- | --- |
| 0:00–0:05 | コールドオープン | 会場写真（柱時計・シャンデリア） | 集められた、15人。／生き残るのは──誰だ。 |
| 0:05–0:13 | 3D：放射状アミダが組み上がる | 生成（Blender） | アミダクジをモチーフにした／リアル交渉ゲーム |
| 0:13–0:18 | 3D：タイトル | 生成（Blender） | 削減アミダクジ／阿弥陀を消して、生き残れ。 |
| 0:18–0:28 | 3D：横線が消え、最短ルートが光り、メダルが積まれる | 生成（Blender） | 横線を消して、中央への〈最短ルート〉を作れ。／最短ルートのプレイヤーのメダルを最も多く持つ者が、勝つ。 |
| 0:28–0:37 | 3D：発表ツール画面が浮かぶ回廊 | 発表ツール（`present.html`）のキャプチャー | 協力か。裏切りか。／嘘と信頼が入り混じる、スリリングな交渉ゲーム。 |
| 0:37–0:48 | 会場写真モンタージュ | 会場写真 8枚 | その言葉は、真実か。／手を組んだ相手が、最後に裏切る。／疑え。信じろ。──そして、出し抜け。 |
| 0:48–0:54 | 3D：投票カードとメダルが卓に落ちる | カードデザイン画像＋生成 | 息を呑む駆け引き。張り詰めた沈黙。／騙し合いの頭脳戦を、その身で。 |
| 0:54–1:04 | キービジュアル → エンドカード | `hero_amida.png`＋生成フレーム | リアル交渉ゲーム／削減アミダクジ／貸切予約 受付中／プレイヤー15名・公演時間 約3時間 |

BGM・効果音（ドローン、時計の秒針、衝撃音、ライザー、心音、オスティナート）は `audio.py` で numpy により合成しています。

## 再生成手順

```bash
python3 -m venv venv && ./venv/bin/pip install bpy pillow   # Blender 5.2 (Python 3.13)
export PROMO_WORK=/path/to/work   # assets/ と render/ を置く作業ディレクトリ
```

1. `PROMO_WORK/assets/drive/` に Google Drive の素材（会場写真 `PXL_*.jpg`、`hero_amida.png`、`9bedb650.png`、`chatgpt_2026-05-18.png`）を置く
2. 発表ツールのキャプチャー：`node capture_present.js ../../present.html $PROMO_WORK/assets/present`（Playwright。認証・Supabase を使わずデモデータで描画）
3. 素材の前処理：`./venv/bin/python prep.py $PROMO_WORK` と `./venv/bin/python prep2.py $PROMO_WORK`
4. 3D カット：`./venv/bin/python scenes3d.py <build|title|rule|screens|cards> $PROMO_WORK/render/<name>`
   （`--res 960 540 --only 1 100` でプレビュー、`--save x.blend` で .blend 保存）
5. 音声：`./venv/bin/python audio.py $PROMO_WORK/assets/audio/score.wav`
6. 編集・書き出し：`./venv/bin/python edit.py 削減アミダクジ_PV.mp4`（`--save edit.blend` で VSE プロジェクト保存）

テロップの文言とタイミングは `timeline.py` にまとめてあります。
