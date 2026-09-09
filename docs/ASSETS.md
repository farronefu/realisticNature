# 使用素材・保存構成

取得・確認日：2026-09-09。

| 素材 | 配布元 | 用途 | ライセンス |
|---|---|---|---|
| Tileable Moss Patches / sfdnqii / 4K | [Quixel Megascans / Fab](https://www.fab.com/listings/a9a94514-dfba-43cb-92bc-c550d79b8d5d) | 地形沿いの苔デカール36枚、岩の上面・斑点状の苔シェーダー | Fab Standard |
| Rock Moss Set 01 / 4K | [Poly Haven](https://polyhaven.com/a/rock_moss_set_01) | 6種類の岩、主役の岩、小石 | CC0 |
| Fern 02 / 4K | [Poly Haven](https://polyhaven.com/a/fern_02) | 4種類のシダ、近景と小道の両脇 | CC0 |
| Shrub 04 / 4K | [Poly Haven](https://polyhaven.com/a/shrub_04) | 下草・低木・樹冠の広葉 | CC0 |
| Fir Tree 01 / 2K | [Poly Haven](https://polyhaven.com/a/fir_tree_01) | 3種類の針葉樹、幹と樹冠 | CC0 |
| Dead Tree Trunk / 4K | [Poly Haven](https://polyhaven.com/a/dead_tree_trunk) | 倒木・折れ枝 | CC0 |
| Pine Roots / 2K | [Poly Haven](https://polyhaven.com/a/pine_roots) | 樹木の根元 | CC0 |
| Moss 01 / 2K | [Poly Haven](https://polyhaven.com/a/moss_01) | 岩の表面に沿う立体の苔 | CC0 |
| Forest Leaves 02 / 4K | [Poly Haven](https://polyhaven.com/a/forest_leaves_02) | 地面の色・法線・粗さ・実変位 | CC0 |
| Bark Brown 01 / 4K | [Poly Haven](https://polyhaven.com/a/bark_brown_01) | 根と細枝の粗さ。色と微細な凹凸は専用シェーダーで補正 | CC0 |
| Forest Slope / 4K HDR | [Poly Haven](https://polyhaven.com/a/forest_slope) | 環境照明 | CC0 |

地形、曲がる小道、巻いた落ち葉、先細りの根・枝、カメラと配置は、この制作で構築しています。樹木・岩・シダを新規にスキャンしたという意味ではありません。

## Megascans

ユーザーの明示的な承認に基づいてFabのEULAに同意。ユーザーが示した `tileable_moss_patches_sfdnqii_4k.zip` を読み込み、`assets/megascans/moss/` に展開しました。公開Gitには素材の画像を含めず、シェーダーから外部参照します。

完成したPNGなどのリニアメディアと素材本体は別扱いです。素材単体の再配布制限、共同制作での共有の範囲は [Fabの規約](https://www.fab.com/eula) を参照してください。

## 相対パス

シーンは `scenes/ForestPath.blend` から `../assets/` 以下を参照します。ローカルでは素材を用意済み。リポジトリだけを別の環境に持ち出す場合はREADMEに従って素材を復元します。Blenderの「外部データをパック」でMegascansの画像を取り込んだファイルを、そのまま公開Gitにアップロードしないでください。

CC0素材を過去のローカル取得から再利用した記録は `reused_assets.json`、今回追加で取得した記録は `download_manifest.json` にあります。
