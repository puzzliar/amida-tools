# 削減アミダクジ プロモーション動画（Blender）

`削減アミダクジ_PV.mp4` — 1920×1080 / 30fps / 64秒 / H.264 + AAC

Blender 5.2（`bpy` モジュール、Cycles）で 3D カットを生成し、Blender の Video Sequence Editor で写真・テロップ・音声と合わせて書き出しています。

## 構成（絵コンテ）

| 時間 | カット | 素材 | テロップ |
| --- | --- | --- | --- |
| 0:00–0:05 | コールドオープン | 会場写真（柱時計・シャンデリア） | 集められた、15人。／生き残るのは──誰だ。 |
| 0:05–0:13 | 3D：放射状アミダが組み上がる | 生成（Blender） | アミダクジをモチーフにした／リアル交渉ゲーム |
| 0:13–0:18 | 3D：タイトル（ロゴはキービジュアルから切り出した公式ロゴ） | 生成（Blender）＋`hero_amida.png` | 削減アミダクジ／阿弥陀を消して、生き残れ。 |
| 0:18–0:28 | 3D：横線が消え、最短ルートが光り、メダルが積まれる | 生成（Blender） | 横線を消して、中央への〈最短ルート〉を作れ。／最短ルートのプレイヤーのメダルを最も多く持つ者が、勝つ。 |
| 0:28–0:31 | 3D：発表ツール画面が浮かぶ回廊（パネルに寄る） | 発表ツール（`present.html`）のキャプチャー | 協力か。裏切りか。 |
| 0:31–0:45 | 実写（スローモーション＋粒子ノイズ・明滅・グリッチ）：ポーカーチップのケースを開ける → 黒スーツの男がチップを渡す（手元に寄せ、顔は画面外）→ 手から手へチップを渡す（手元を追って中央に寄せ、背景をぼかす） | 会場動画 4本（`PXL_20261017_040954247` ほか） | 嘘と信頼が入り混じる、スリリングな交渉ゲーム。／その言葉は、真実か。／手を組んだ相手が、最後に裏切る。 |
| 0:45–0:48 | 会場写真モンタージュ | 会場写真 3枚 | 疑え。信じろ。──そして、出し抜け。 |
| 0:48–0:54 | 3D：投票カードとメダルが卓に落ちる | カードデザイン画像＋生成 | 息を呑む駆け引き。張り詰めた沈黙。／騙し合いの頭脳戦を、その身で。 |
| 0:54–1:04 | キービジュアル（0:55 から下部に予約プレート、右上に QR コード） | `hero_amida.png`＋生成プレート | 貸切予約 受付中／詳細・ご予約は puzzliar.jp（URL は `timeline.py` の `BOOKING_URL`） |

BGM は `music.py` で作曲・合成したオリジナル曲です（120 BPM・イ短調。スタッカートの弦オスティナート、冷たいピアノのモチーフ、4つ打ちのキック、ヒットに合わせたブラスのスタブ、0:28 のグリッチ・スタッター、スロー区間のハーフタイム）。小節頭が偶数秒に来るので、`timeline.py` のヒットとカット点はすべて拍の上に乗ります。
効果音（時計の秒針、衝撃音、ライザー、ホワイトノイズ、スロー区間のテープストップ・ノイズ・グリッチ音）は `audio.py` で合成し、`music.py` の曲と合わせてミックスしています。

## 再生成手順

```bash
python3 -m venv venv && ./venv/bin/pip install bpy pillow numpy scipy "qrcode[pil]"   # Blender 5.2 (Python 3.13)
export PROMO_WORK=/path/to/work   # assets/ と render/ を置く作業ディレクトリ
```

1. `PROMO_WORK/assets/drive/` に Google Drive の素材（会場写真 `PXL_*.jpg`、`hero_amida.png`、`9bedb650.png`、`chatgpt_2026-05-18.png`）を置く
2. 発表ツールのキャプチャー：`node capture_present.js ../../present.html $PROMO_WORK/assets/present`（Playwright。認証・Supabase を使わずデモデータで描画）
3. 素材の前処理：`./venv/bin/python prep.py $PROMO_WORK` と `./venv/bin/python prep2.py $PROMO_WORK`
   - 実写カット：Drive の動画（`PXL_20261017_04*.mp4`）を `PROMO_WORK/assets/drive_video/` に置き、`python3 prep3.py $PROMO_WORK`（ffmpeg で 30fps の連番 JPEG に切り出し、動き補間でスロー化し、`FOCUS` 指定のカットは手元を追跡して寄り＋背景ぼかし、粒子ノイズ・明滅・グリッチを焼き込み。使用区間と速度は `timeline.py` の `CLIPS`）
4. 3D カット：`./venv/bin/python scenes3d.py <build|title|rule|screens|cards> $PROMO_WORK/render/<name>`
   （`--res 960 540 --only 1 100` でプレビュー、`--save x.blend` で .blend 保存）
5. 音声：`./venv/bin/python audio.py $PROMO_WORK/assets/audio/score.wav`
6. 編集・書き出し：`./venv/bin/python edit.py master.mp4`（`--save edit.blend` で VSE プロジェクト保存）
7. 仕上げ：`./finish.sh master.mp4 削減アミダクジ_PV.mp4`（グレード後に 0:31–0:48 へ粒子ノイズを足し、2パス 9Mbps で書き出し）

テロップの文言とタイミングは `timeline.py` にまとめてあります。
