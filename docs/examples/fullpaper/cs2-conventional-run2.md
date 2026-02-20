# CS2 条件A: Conventional — マルチテナントSaaSセッション管理 (Run 2)

> **Run**: CS2-A-Run2
> **Date**: 2026-02-20
> **Thread**: 新規 (Codex MCP: 019c79b3-c712-7f33-ac44-46e92f1c5b91)
> **Model**: GPT-5.2 (via Codex)

---

**推奨設計（結論）**
「**短寿命JWT + Redis中心のセッション制御 + ローカルキャッシュ**」のハイブリッド構成が最適です。
JWTだけで完全ステートレスにすると即時無効化が弱く、毎回DB照会は遅いためです。

**要件への対応**
- 同時ログイン: 端末ごとに `session_id (sid)` を発行し、1ユーザーに複数セッションを保持します。
- 管理者の即時無効化: `user_session_version`（または `revoked_after`）をユーザー単位で持ち、無効化時に原子的に更新します。既存トークンは次リクエストで即不一致になり拒否されます。
- 水平スケール: 認証サーバーをステートレス化し、共有状態は Redis Cluster に集約します（LBでスケール容易）。
- 低レイテンシ: 署名検証は各ノードでローカル実行、Redis参照は `MGET` と L1キャッシュで最小化します。

**データモデル（最小）**
- JWT Claims: `tid(tenant)`, `sub(user)`, `sid`, `ver`, `exp`
- Redis:
  - `user_ver:{tid}:{uid}` → 現在バージョン
  - `sess:{tid}:{sid}` → `active/revoked`, TTL
- 永続DB: 監査用の `sessions` 履歴（ログイン端末、IP、失効理由など）

**認証フロー**
1. JWT署名・`exp` をローカル検証
2. `token.ver` と `user_ver:{tid}:{uid}` を比較（L1→Redis）
3. 必要なら `sess:{tid}:{sid}` も確認
4. 一致なら許可、不一致なら 401

**管理者失効フロー（ユーザー単位）**
1. `INCR user_ver:{tid}:{uid}`（これで全端末即時失効）
2. Pub/Subで各認証ノードのL1キャッシュを即時破棄
3. DBへ監査ログを非同期反映

**設計上の注意**
- マルチテナント分離のため、全キーと索引に `tenant_id` を必須化してください。
- Access Token は短寿命（例: 2〜5分）、Refresh Token はローテーション方式にしてください。
- 「即時」を担保するなら、認証可否の最終判定はRedis値を基準にしてください（L1は短TTL＋イベント失効）。

必要であれば次に、Redisキー設計・API仕様（`/admin/users/{id}/revoke` など）・擬似コードまで具体化します。
