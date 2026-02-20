# CS2 条件A: Conventional — マルチテナントSaaSセッション管理 (Run 3)

> **Run**: CS2-A-Run3
> **Date**: 2026-02-20
> **Thread**: 新規 (Codex MCP: 019c7994-c542-7b60-9c99-199307548d18)
> **Model**: GPT-5.2 (via Codex)

---

要件の衝突点は、`即時失効` と `低レイテンシ` です。
この条件では、**短命JWT + Redisセッション台帳 + 失効イベント配信**のハイブリッド構成が実務的です。

**提案アーキテクチャ**
- アプリサーバ: ステートレス（水平スケール容易）
- Redis Cluster: セッションの正本
- Pub/Sub（Redis Streams/Kafka等）: 失効通知の即時配信
- 各サーバのローカルキャッシュ: 認証結果を短時間保持（失効通知で即削除）

**データモデル（例）**
- `sess:{tenant_id}:{sid}`: `user_id`, `device_id`, `status(active/revoked)`, `expires_at`
- `user_sess:{tenant_id}:{user_id}`: `sid`集合
- `user_ver:{tenant_id}:{user_id}`: 強制失効用バージョン
- Access Token(JWT): `tenant_id`, `user_id`, `sid`, `user_ver`, `exp(1〜5分)`

**認証フロー**
1. JWT署名・期限をローカル検証（I/Oなし）
2. `sid`状態をローカルキャッシュ確認（ミス時のみRedis参照）
3. トークン内`user_ver`と現在`user_ver`一致で許可

**管理者による即時無効化**
- ユーザー全端末無効化: `INCR user_ver` + 失効イベント配信
- 特定端末のみ無効化: 対象`sid`を`revoked`更新 + イベント配信
- 各サーバはイベント受信時に該当キャッシュを即削除

**要件との対応**
- 複数端末同時ログイン: `sid`を端末単位で発行して共存
- 即時無効化: バージョン更新 + 配信でほぼリアルタイム反映
- 水平スケール: サーバは無状態、Redis共有
- 低レイテンシ: 通常はローカル検証 + キャッシュヒットで最小化

必要であれば、次にこの設計のシーケンス図とRedisキー設計（TTL/更新戦略）まで具体化します。
