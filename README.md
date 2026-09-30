# 江東・本免学科試験のクラウド監視

GitHub Actionsで5分ごとに江東運転免許試験場の学科試験枠を確認し、空きがあればGmailに通知します。PCを閉じても実行できます。予約は行いません。

## セットアップ

1. GitHubにこのフォルダーの内容をリポジトリのルートへ配置します。ワークフローは `.github/workflows/watch.yml` に置きます。
2. リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で次を登録します。値をコードやIssueに書かないでください。

   - `GMAIL_ADDRESS`：送信元のGmailアドレス
   - `GMAIL_APP_PASSWORD`：Googleのアプリ パスワード
   - `MAIL_TO`：通知先メールアドレス

3. [Gmailのアプリ パスワード](https://support.google.com/mail/answer/185833?hl=ja)を発行し、`GMAIL_APP_PASSWORD` に登録します。アプリ パスワードはチャットや公開リポジトリに書かないでください。
4. **Actions → Koto written exam slot watch → Run workflow** で認証情報不要のカレンダー接続テストを実行し、ログを確認します。
5. リポジトリの **Settings → Secrets and variables → Actions → Variables** に `ENABLE_WATCH` を `true` で登録します。ここから5分間隔の通知監視が始まります。最初の通知監視で状態管理用のGitHub Issueを1件作り、既存の空き枠があればメールに通知します。手動で監視処理を1回試す場合は、Run workflow の `Run the email watch once` を有効にします。

日付を絞る場合はワークフロー内の `START_DATE` と `END_DATE` に `YYYY-MM-DD` を設定します。未設定なら実行日から90日先までです。午前だけなら `TIME_OF_DAY: morning`、午後だけなら `TIME_OF_DAY: afternoon` とします。

## 運用上の注意

- 公開リポジトリの標準GitHubランナーは無料です。コード・ワークフロー・通知状態のIssueは公開されるため、認証情報や個人情報を入れないでください。[GitHub Actionsの料金](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- GitHubの定期実行は遅延する場合があり、時刻どおりの通知は保証されません。公開リポジトリでは60日間リポジトリに活動がないと定期実行が無効になります。[スケジュールの仕様](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- 監視は受験条件に合う方だけが使用してください。[警視庁の学科試験案内](https://www.keishicho.metro.tokyo.lg.jp/menkyo/menkyo/web.html)
