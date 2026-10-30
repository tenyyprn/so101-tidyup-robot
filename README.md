# 見て、つかんで、片付ける ― SO101 片付けロボットアーム

ID:Y-ORIHARA

Physical AI 応用編1 最終課題。低価格ロボットアーム **SO101** に、**模倣学習(LeRobot)** で「机の上の黒いスポンジ3個を白い箱へ片付ける」作業を覚えさせた。

- 人がリーダーアームで示したお手本を、**上からのカメラと手首カメラの2台**で録画して学習した(112 回分)。
- ACT では、ランダムな並べ方で **2つのスポンジの「間」(何もない場所)をつかむ**失敗が 75% の回で起きた。答えが2つある場面(講義 第3回・第7回の「多峰性」)で、1つの行動しか出せない方策が中間に寄ったという仮説を立てた。
- **同じデータで Diffusion Policy に変えると、「間」をつかむ失敗は 0% になり、箱に入ったスポンジは 48% から 85% に上がった。**

- デモ動画:https://youtu.be/zCo2obT3ASg
- コード:https://github.com/tenyyprn/so101-tidyup-robot
- 学習済みモデル(Hugging Face):
  - Diffusion Policy:https://huggingface.co/tenyyprn/so101-tidyup-diffusion
  - ACT(比較用):https://huggingface.co/tenyyprn/so101-tidyup-act

## 結果

### ACT と Diffusion Policy の比較(ランダムな並べ方)

同じ 112 回分のデータで学習し、同じ4つのランダム配置(マス ②④⑧、③④⑧、①⑤⑦、②⑤⑨)で各 5 回、計 20 回ずつ試した。

| 指標 | ACT-112 | Diffusion Policy |
| --- | --- | --- |
| 「間」をつかんだ回 | 15 / 20(75%) | **0 / 20(0%)** |
| 箱に入ったスポンジ | 29 / 60(48%) | **51 / 60(85%)** |
| 3個とも片付けた回 | 3 / 20(15%) | **15 / 20(75%)** |
| 定型配置 A(参考、各 5 回) | 13 / 15(87%) | 13 / 15(87%) |

Diffusion Policy に残った失敗は、時間切れ(3 回)と、1つのスポンジのすぐ横で空をつかみ続ける位置合わせのずれ(2 回)だった。

3個のお手本だけで学習した Diffusion Policy に4〜9個を片付けさせると、どの個数でも全部片付けた回があった(4個は 3 回中 3 回。5個以上は箱があふれるため、人が箱の中身を押し込む・空にする手伝いをした)。

動画の倍速は実時間に対する倍率。Diffusion Policy は推論中に記録が止まり、記録映像が実時間の約 0.77 倍に縮むため、`video/make_video.py` で映像ごとに補正している。

### ACT の改善の経緯(並べ方ごと)

3個のスポンジを続けて片付けたときの、箱に入った割合(各並べ方 5 回。A の ACT-58 のみ、接続エラーで止まった1回を除く 9 回)。

| 並べ方 | 最初に試したモデル | 最新のモデル | 3個とも片付けた回(最新) |
| --- | --- | --- | --- |
| A 手前の列 | 78%(ACT-58) | 87%(ACT-112) | 4 / 5 |
| B 左の列 | 87%(ACT-94) | 93%(ACT-112) | 4 / 5 |
| C 斜め | 67%(ACT-94) | 80%(ACT-112) | 3 / 5 |
| D 奥の列 | 0%(ACT-58) | 87%(ACT-104) | 4 / 5 |
| ランダム | 0%(ACT-58) | 47%(ACT-104) | 0 / 5 |

詳しい経緯と分析は `docs/` のレポートにまとめた。

- `docs/PhysicalAI_応用編1_最終課題レポート_SO101.pdf` ― **最終課題レポート(提出版)**
- `docs/ACT_実験結果と学び_SO101_20261024.pdf` ― ACT の結果と学びのまとめ
- `docs/PhysicalAI_中間レポート_SO101_20261024.pdf` ― 中間レポート
- `docs/PhysicalAI_仮レポート_SO101.pdf` ― 初期の仮レポート(10月18日)
- `docs/eval_results.csv`、`docs/eval_pick3.csv` ― 実機テストの全記録

## 構成

| 区分 | 使ったもの |
| --- | --- |
| ロボット | SO101 フォロワーとリーダー(Feetech STS3215 サーボ × 6 ずつ) |
| カメラ(上) | Logicool C920、640×480・30fps |
| カメラ(手首) | Inno-Maker U20CAM-1080P(広角)、640×480・約29fps、電源付き USB ハブ経由 |
| 計算機 | NVIDIA GB10(DGX Spark) |
| ソフトウェア | LeRobot 0.6.1(ACT、Diffusion Policy、SmolVLA)、ffmpeg |

## ファイル

| ファイル | 役割 |
| --- | --- |
| `cameras.sh` | カメラ設定の共通定義。手首カメラのフレームレート低下の防止、接続エラー時の自動リトライ |
| `teleop.sh` | リーダーで操作する練習(録画なし) |
| `preview.sh [top\|wrist]` | カメラの向き合わせ |
| `record.sh <名前> <回数> "<タスク>" [リセット秒] [録画秒]` | 2台のカメラでお手本を録画 |
| `review.sh [データ名]` | 録画の確認。横並び動画、各回の最初4秒・最初と最後のコマの一覧、動いていない回の検出 |
| `train.sh <データ名> [ステップ]` | ACT をゼロから学習 |
| `finetune.sh <元モデル> <データ名> [ステップ]` | 学習済み ACT を出発点に追加学習(約4時間→約1.5時間) |
| `train_diffusion.sh <データ名> [ステップ] [バッチ]` | Diffusion Policy を学習(240×320、95% ランダム切り抜き、DDIM 10 ステップ、64 コマ予測・16 コマ実行) |
| `train_smolvla.sh <データ名> [ステップ] [バッチ]` | SmolVLA を学習(カメラ名を camera1/camera2 に読み替え) |
| `run_policy.sh <モデル> [秒] ["<タスク>"]` | 学習したモデルで自律動作(ACT・Diffusion Policy・SmolVLA 対応、1回の動きを 10° に制限) |
| `film_policy.sh <モデル> <名前> [回数] [秒]` | 自律動作しながら映像を保存(デモ動画用) |
| `make_demo.sh <データ名> [--delete-wrist]` | 上からのカメラだけでデモ動画を作る(手首カメラは部屋が映るため使わない) |
| `policy_sensitivity.py` | 入力(画像・姿勢)を入れ替えて、モデルが何を見ているかを調べる |
| `policy_reach_test.py` | 各回の最初の場面から、取りに行く向き(肩の回転)の予測をお手本と比べる |
| `voice_test.py` | マイクと Whisper(音声認識)の確認 |
| `video/make_video.py`、`video/storyboard.json` | 絵コンテから字幕付きの動画(3分)を組み立てる |

## セットアップ

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install "lerobot[viz,dataset,training,smolvla,diffusion]==0.6.1" faster-whisper sounddevice soundfile
```

ポートはシリアル番号の固定パス(`/dev/serial/by-id/...`)、カメラは `/dev/v4l/by-id/...` で指定している。自分の環境に合わせて `cameras.sh` と各スクリプトのパスを書き換える。

キャリブレーション(初回のみ):

```bash
lerobot-calibrate --robot.type=so101_follower --robot.port=<フォロワーのポート> --robot.id=my_follower
lerobot-calibrate --teleop.type=so101_leader --teleop.port=<リーダーのポート> --teleop.id=my_leader
```

## 使い方の流れ

```bash
./preview.sh top                                   # 1. カメラの向きを合わせる
./record.sh so101_pick3 10 "Put all the black sponges in the white box" 20 35   # 2. お手本を録画
./review.sh                                        # 3. 録画を確認(手の映り込み・片付け残しの回は除外)
lerobot-edit-dataset --operation.type merge ...    # 4. 録画をまとめる
./train.sh so101_all94 50000                       # 5. 学習(または ./finetune.sh で追加学習)
./run_policy.sh so101_all112_ft 45                 # 6. 自律動作でテスト
./film_policy.sh so101_all112_ft patternA 3 45     # 7. デモ映像の撮影
./make_demo.sh rollout_patternA_<日時> --delete-wrist
```

## 学び

- **映っているものは、すべて学習される**。手の映り込みやカメラのずれを含むデータを足すと、モデルは画像を信用せず、アームの姿勢に頼った。
- **量より、狙いを絞った質**。苦手だった奥の列は、お手本を 10 回足すだけで 0% から 87% になった。
- **お手本の癖まで真似される**。「つかむ前に一瞬止まる」動きをロボットが再現した。
- **学習の誤差が小さいことは、使えることを意味しない**。入力を入れ替える実験で、モデルが何を見ているかを確かめた。
- **答えが2つある場面では、ACT は中間に寄った**。行動の分布を学習する Diffusion Policy に変えると、同じデータでこの失敗がなくなり、多峰性の仮説を強く支持する結果になった(ACT の内部で何が起きているかの断定には追加の分析が必要)。モデルは LeRobot 0.6.1 の実装をそのまま使い、データの設計・評価・分析を自分で行った。
- **SmolVLA は「間」はつかまなかったが、つかめなかった**(学習量 30,000 ステップ × バッチ 8 では精度が不足)。

## 今後の展望

1. **生成モデル型の方策を比べ続ける**:Diffusion Policy に加え、DiT(Flow Matching)と、1〜2回の計算で行動を出す MeanFlow を試し始めている。予備的な実機試験では、記録データ上のずれが小さいモデルが実機でも成功するとは限らず(DiT 1.86° < DP 2.7° だが、実機の成功は DP が上)、お手本データの変え方で DP と DiT の結果が逆になった。MeanFlow は2回の計算でも実機で動きが不安定だった。今後は開始姿勢をそろえた評価手順を固定し、データの変更を1つずつ試して原因を切り分ける。
2. **双腕に広げる**:LeRobot は SO101 の双腕構成(`bi_so_follower` / `bi_so_leader`)に対応している。アームをもう1組加え、片手で箱を押さえてもう片手で入れる、手から手へ受け渡す、といった片付け作業に挑戦する。行動が12次元になり「どちらの手から動くか」の選び方も増えるため、本課題で見た多峰性の問題がより強く現れ、DP・Flow Matching・MeanFlow の違いを確かめる題材になる。

## AI の活用

開発は Claude Code(Anthropic)と対話しながら進めた。不具合の診断(キャリブレーションの値の回り込み、USB の電力不足、通信エラー)、スクリプトと分析ツールの作成、録画の品質チェック、実験計画を AI が担い、実機の操作・配線・お手本の操作・最終判断は人が行った。

## 含まれていないもの

録画データ(約 100 エピソード)と仮想環境は含めていない。録画データは手首カメラに部屋が映るため公開しない。学習済みモデル(合計 約 28GB)のうち、比較に使った2つ(Diffusion Policy と ACT-112)は上の Hugging Face で公開している。

## 参考文献

1. LeRobot(Hugging Face): https://github.com/huggingface/lerobot
2. ACT: T. Z. Zhao, V. Kumar, S. Levine, C. Finn. "Learning Fine-Grained Bimanual Manipulation with Low-Cost Hardware." arXiv:2304.13705, 2023.
3. Diffusion Policy: C. Chi, Z. Xu, S. Feng, E. Cousineau, Y. Du, B. Burchfiel, R. Tedrake, S. Song. "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion." arXiv:2303.04137, 2023.
4. DDIM: J. Song, C. Meng, S. Ermon. "Denoising Diffusion Implicit Models." ICLR 2021. arXiv:2010.02502.
5. SmolVLA: M. Shukor ほか. "SmolVLA: A Vision-Language-Action Model for Affordable and Efficient Robotics." arXiv:2506.01844, 2025.
6. SO-101(LeRobot ドキュメント): https://huggingface.co/docs/lerobot/so101
7. npaka「SO-101 入門 (1) - キットの入手」(最終課題サンプル): https://note.com/npaka/n/nfaa9db0834e5
8. Physical AI 講座 2026 応用編1 第3回・第7回 講義資料(多峰性と Diffusion Policy の説明を参考にした)
