# PhishOps - フィッシュオプス

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Terraform](https://img.shields.io/badge/terraform-1.0%2B-purple)
![Platform](https://img.shields.io/badge/cloud-Tencent%20Cloud-blue)
![Status](https://img.shields.io/badge/status-production%20ready-success)

**Gophish カスタム強化版をクラウドに高速デプロイ**

[GophishModified](https://github.com/25smoking/GophisModified) カスタム版に基づく

[中文](README.md) | [English](README_EN.md)

</div>

![Deployment Success](assets/deployment_success.png)

---

## 📖 プロジェクト概要

**PhishOps (フィッシュオプス)** は、CI/CD フローを通じて拡張版 GophishModified プラットフォームをワンクリックで展開できる Gophish 自動化デプロイツールです。煩雑なセットアップの問題を解決し、コスト効率を大幅に向上させます。

> 💡 **GophishModified について**  
> このプロジェクトは [GophishModified](https://github.com/25smoking/GophisModified) カスタム版を展開します。以下の機能が含まれます：
> - QR コード生成（EvilGophish からインスピレーション）
> - その他のカスタム機能...

### ✨ 主な機能

- **🚀 ワンクリックデプロイ** - 3分以内に完全自動化されたインフラストラクチャーのプロビジョニング
- **☁️ Tencent Cloud 最適化** - Tencent Cloud（香港、広州リージョン）での完全テスト済み展開
- **🔄 GitOps ワークフロー** - GitHub からの継続的デリバリー、ブランチ切り替えサポート
- **🎨 強化機能** - GophishModified のカスタム修正
- **🔒 セキュリティ第一** - 自動ファイアウォール設定、HTTPS サポート、パスワード自動生成
- **💾 スマートバックアップ** - リソース削除前の自動データベースバックアップ
- **📊 コスト透明性** - リアルタイムリソース監視とコスト見積もり

### 🎯 使用例

- **セキュリティ意識向上トレーニング** - 従業員向けフィッシングメール識別訓練
- **レッドチームオペレーション** - 攻撃シミュレーションとインシデント対応演習
- **ペネトレーションテスト** - ソーシャルエンジニアリングテストシナリオ
- **セキュリティリサーチ** - フィッシング技術研究と防御メカニズムの検証

---

## 🛠️ 環境準備

### 1. Tencent Cloud アカウント

Tencent Cloud API 認証情報を取得：

- **コンソール**: [API キー管理](https://console.cloud.tencent.com/cam/capi)
- **推奨リージョン**:
  - `ap-hongkong` - 香港（国際）
  - `ap-guangzhou` - 広州（中国本土）
  - `ap-shanghai` - 上海（中国本土）

> 💡 **実験的サポート**  
> このプロジェクトは **Tencent Cloud で完全にテスト済み**です。~~Alibaba Cloud と Huawei Cloud の設定ファイルは準備されていますが、完全にはテストされていません。ご自身の責任でご使用ください。~~

### 2. ローカルツールのインストール

**Chocolatey による一括インストール（Windows 推奨）**

1. PowerShell を**管理者として**開く
2. Chocolatey をインストール（まだインストールされていない場合）：
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

3. すべての依存関係をインストール：
   ```powershell
   choco install python terraform git openssh -y
   ```

4. インストールを確認：
   ```powershell
   python --version    # Python 3.8+ が表示されるはず
   terraform -v        # Terraform 1.0+ が表示されるはず
   git --version       # Git バージョンが表示されるはず
   ssh -V             # OpenSSH バージョンが表示されるはず
   ```

---

## 🚀 クイックスタート

### ステップ 1：リポジトリをクローン

```bash
git clone https://github.com/25smoking/PhishOps.git
cd PhishOps
```

### ステップ 2：認証情報を設定

```powershell
# 設定テンプレートをコピー
copy configs\.env.example configs\.env

# 設定ファイルを編集
notepad configs\.env
```

**設定例：**

```ini
# Tencent Cloud
TENCENT_CLOUD_SECRET_ID=your_secret_id
TENCENT_CLOUD_SECRET_KEY=your_secret_key

# オプション：アベイラビリティゾーンを指定（リソース不足の場合）
# TENCENT_CLOUD_AVAILABILITY_ZONE=ap-hongkong-3

# オプション：カスタム SSH キーパス（デフォルトは ~/.ssh/id_rsa）
# SSH_KEY_PATH=$HOME/.ssh/id_rsa
```

> ⚠️ **Windows ユーザー注意**  
> Windows では、パス内の `$HOME` が自動的にユーザーディレクトリに展開されます（例：`C:\Users\YourName`）

### ステップ 3：クラウドにデプロイ

**Tencent Cloud（香港）にデプロイ**
```powershell
python scripts/deploy.py -p tencent -r ap-hongkong
```

**Tencent Cloud（広州）にデプロイ**
```powershell
python scripts/deploy.py -p tencent -r ap-guangzhou
```

**特定の GitHub ブランチをデプロイ**
```powershell
python scripts/deploy.py -p tencent -r ap-hongkong -b master
```

### ステップ 4：デプロイ完了を待つ

スクリプトは以下を自動的に完了します（約 3〜5 分）：

1. ✅ クラウドインフラストラクチャーの作成（VPC、セキュリティグループ、サーバーインスタンス）
2. ✅ SSH サービスの準備完了を待つ
3. ✅ Docker と Go 環境をインストール
4. ✅ GitHub からソースコードを取得してコンパイル
5. ✅ 外部アクセスを設定（0.0.0.0 でリッスン）
6. ✅ Gophish サービスを起動

**デプロイ成功時の出力：**

```text
========================================================
🎉 Gophish のデプロイが成功しました！
========================================================

📍 アクセス情報:
   管理パネル: https://1.2.3.4:3333
   フィッシングサイト: http://1.2.3.4

🔑 管理者ログイン:
   ユーザー名: admin
   パスワード: a1b2c3d4e5f6

🖥️  SSH アクセス:
   コマンド: ssh -i ~/.ssh/id_rsa root@1.2.3.4

💰 推定コスト: ¥0.15/時間（約 ¥108/月）
========================================================
```

---

## 💻 管理とメンテナンス

### リソースステータスの確認

```powershell
python scripts/check-resources.py
```

### SSH リモートアクセス

```bash
# 自動生成されたキーでログイン
ssh -i ~/.ssh/id_rsa root@<サーバーIP>

# Gophish ログを表示
journalctl -u gophish -f
```

### Gophish サービスの再起動

```bash
systemctl restart gophish
```

---

## 🗑️ リソースの削除

### 標準削除（バックアップ付き）

```powershell
python scripts/destroy.py -p tencent
```

**実行フロー：**
1. 削除操作の確認プロンプト
2. データベースを `backups/` ディレクトリに自動バックアップ
3. すべてのクラウドリソースを削除（サーバー、VPC、セキュリティグループ）
4. ローカルの Terraform ステートファイルをクリーンアップ

### 強制削除（確認スキップ）

```powershell
python scripts/destroy.py -p tencent --force
```

### ⚠️ 重要なお知らせ

> **Terraform Destroy がハングする場合の解決策**  
> `terraform destroy` コマンドが応答しなくなった場合：
> 
> 1. **`Ctrl+C` を押してスクリプトを中断**
> 2. **クラウドコンソールで手動でリソースを削除**：
>    - Tencent Cloud: [CVM コンソール](https://console.cloud.tencent.com/cvm/instance)
>    - 削除順序：インスタンス → セキュリティグループ → VPC
> 3. **ローカルステートをクリーンアップ**：
>    ```powershell
>    cd terraform/tencent
>    rm -rf .terraform terraform.tfstate*
>    ```

⚠️ **警告：** 削除は取り消せません。重要なデータがバックアップされていることを確認してください！

---

## 💰 コスト見積もり

### 時間単位課金（実際の使用時間）

| プラットフォーム | インスタンスタイプ | 時間料金 | 月額料金（720時間） |
|-----------------|-------------------|---------|---------------------|
| Tencent Cloud | SA2.MEDIUM4 (2C4G) | ¥0.15/時間 | ¥108/月 |

> 💡 **節約のヒント：** 演習終了後すぐにリソースを削除 - 実際の使用時間のみ課金（例：2時間使用で ¥0.30 のみ）

---

## 📚 プロジェクト構造

```
phishops/
├── configs/              # 設定ファイル
│   ├── .env.example     # 設定テンプレート
│   └── .env             # 実際の設定（Git にコミットしない）
├── scripts/              # 自動化スクリプト
│   ├── deploy.py        # デプロイスクリプト
│   ├── destroy.py       # 削除スクリプト
│   └── check-resources.py # リソース確認スクリプト
├── terraform/            # Terraform 設定
│   ├── alibaba/         # Alibaba Cloud 設定
│   ├── tencent/         # Tencent Cloud 設定
│   └── huawei/          # Huawei Cloud 設定
├── backups/              # データベースバックアップディレクトリ
├── README.md             # 中国語ドキュメント（メイン）
├── README_EN.md          # 英語ドキュメント
└── README_JP.md          # 日本語ドキュメント
```

---

## ⚠️ 免責事項

このツールは**承認されたセキュリティテストおよび教育目的のみ**を対象としています。ユーザーは以下を遵守する必要があります：

- ✅ 対象システムの所有者から明示的な書面による承認を得る
- ✅ 管轄区域のすべての適用法令を遵守する
- ✅ 違法または悪意のある活動に使用しない
- ✅ 自分の行動とその結果に対して全責任を負う

**無許可のフィッシング攻撃は違法です。作者は悪用に対する責任を負いません。**

---

## 📄 ライセンス

このプロジェクトは [MIT ライセンス](LICENSE) の下でライセンスされています。

---

## 🤝 貢献

貢献を歓迎します！Issue や Pull Request をお気軽に送信してください。

1. このプロジェクトに Star を付ける
2. プロジェクトを Fork する
3. 機能ブランチを作成 (`git checkout -b feature/new-feature`)
4. 変更をコミット (`git commit -m 'Add new feature'`)
5. ブランチにプッシュ (`git push origin feature/new-feature`)
6. Pull Request を開く

---

## 📞 連絡先

- **プロジェクトホーム**: [https://github.com/25smoking/PhishOps](https://github.com/25smoking/PhishOps)
- **Issue Tracker**: [GitHub Issues](https://github.com/25smoking/PhishOps/issues)

---

<div align="center">

**このプロジェクトが役に立った場合は、⭐ Star をお願いします！**

セキュリティ研究者により ❤️ を込めて作成

</div>
