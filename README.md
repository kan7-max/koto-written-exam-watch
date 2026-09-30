# 江東・本免学科試験のクラウド監視

GitHub Actionsが5分ごとに江東運転免許試験場の本免学科試験枠を確認します。空きが出たら担当者付きGitHub Issueを作成し、GitHubの通知設定を通じてメールで知らせます。PCを閉じても実行できます。予約は行いません。

## セットアップと確認

1. GitHubアカウントの[通知設定](https://github.com/settings/notifications)で、通知先メールアドレスと「Participating, @mentions and custom」の Email を確認します。
2. **Actions → Koto written exam slot watch → Run workflow** で `test_notification` を有効にして実行すると、テスト用Issueが1件作られ、リポジトリ所有者に割り当てられます。GitHubからのメールを確認してください。
3. **Settings → Secrets and variables → Actions → Variables** に `ENABLE_WATCH=true` を登録します。定期監視が始まります。`run_watch` を有効にして手動確認もできます。

GmailのパスワードやAPIキーの登録は不要です。GitHub Actions付属の `GITHUB_TOKEN` でIssueを作ります。既存の `GMAIL_ADDRESS` と `MAIL_TO` は使用しません。

日付を絞る場合はワークフロー内の `START_DATE` と `END_DATE` に `YYYY-MM-DD` を設定します。未設定なら実行日から90日先までです。午前だけなら `TIME_OF_DAY: morning`、午後だけなら `TIME_OF_DAY: afternoon` とします。

## 運用上の注意

- リポジトリとIssueは公開です。空き枠の日時はIssueに表示されます。個人情報や認証情報は書き込みません。
- GitHubの通知メールはアカウントの通知設定、メールの振り分け、GitHub側の配信状況に依存します。[通知設定の説明](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications)
- GitHubの定期実行は遅延する場合があり、時刻どおりの通知は保証されません。公開リポジトリでは60日間リポジトリに活動がないと定期実行が無効になります。[スケジュールの仕様](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- 監視は受験条件に合う方だけが使用してください。[警視庁の学科試験案内](https://www.keishicho.metro.tokyo.lg.jp/menkyo/menkyo/web.html)
