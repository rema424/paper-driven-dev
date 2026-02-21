# CS2 条件A: Conventional — マルチテナントSaaSセッション管理 (Run 2)

> **Run**: CS2-A-Run2
> **Date**: 2026-02-22
> **Model**: Claude Sonnet 4.6
> **Context**: Fresh agent invocation

---

# マルチテナントSaaSセッション管理システム設計分析

## 1. 問題の整理と制約分析

### 1.1 要件間のトレードオフ

要件を整理すると、根本的なトレードオフが存在する。

**複数端末同時ログイン** と **即時セッション無効化** の組み合わせは、セッションの識別粒度とストレージ設計を複雑にする。単一のユーザーセッションではなく、ユーザーごとに複数のセッショントークンを管理する必要がある。

**水平スケーリング** と **低レイテンシ認証** は、インメモリ状態の共有問題を引き起こす。スケールアウトしたサーバーが同一のセッション状態を参照できなければならない。

**即時無効化** と **低レイテンシ** は、キャッシュ戦略と一貫性保証のトレードオフを生む。キャッシュを長く保持すれば認証は速くなるが、無効化の即時性が損なわれる。

### 1.2 マルチテナント固有の制約

テナント間の完全な分離が求められる。セッション管理においては以下を保証する必要がある。

- テナントAのユーザーがテナントBのリソースにアクセスできない
- あるテナントの管理者が別テナントのセッションを操作できない
- テナント単位の監査ログ

---

## 2. アーキテクチャ設計

### 2.1 セッションモデル

#### トークン構造

JWTと参照トークンのハイブリッドアプローチを採用する。

```
[アクセストークン] - 短命JWT (有効期限: 5分)
  ペイロード:
    - session_id: セッション固有ID
    - tenant_id: テナントID
    - user_id: ユーザーID
    - device_id: 端末ID
    - exp: 有効期限
    - jti: JWT固有ID

[リフレッシュトークン] - 不透明トークン (有効期限: 30日)
  - セキュアランダム文字列 (256bit)
  - Redis/DBに保存
```

この設計の根拠:

- **アクセストークンを短命JWTにする理由**: 検証がサーバーレスで行えるためレイテンシが最小化できる。期限切れ前に無効化する必要がある場合、最大で5分の遅延を受け入れる設計判断とする
- **リフレッシュトークンを不透明トークンにする理由**: 長命なセッション継続性を管理しつつ、即時無効化の操作対象をここに限定できる

#### セッションエンティティ

```
Session {
  session_id:    UUID           -- セッション固有ID
  tenant_id:     UUID           -- テナントID
  user_id:       UUID           -- ユーザーID
  device_id:     String         -- 端末識別子
  device_name:   String         -- 端末表示名 ("iPhone 15", "Chrome on Mac")
  refresh_token_hash: String    -- ハッシュ化済みリフレッシュトークン
  created_at:    Timestamp
  last_active_at: Timestamp
  expires_at:    Timestamp
  revoked_at:    Timestamp?     -- NULL = 有効
  ip_address:    String
  user_agent:    String
}
```

### 2.2 ストレージ層設計

#### プライマリストレージ: PostgreSQL

テナント分離とACIDの保証を優先する。

```sql
-- テナントごとのスキーマ分離 or Row-Level Security
-- Row-Level Security アプローチを採用

CREATE TABLE sessions (
  session_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id         UUID NOT NULL,
  user_id           UUID NOT NULL,
  device_id         TEXT NOT NULL,
  device_name       TEXT,
  refresh_token_hash TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_active_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at        TIMESTAMPTZ NOT NULL,
  revoked_at        TIMESTAMPTZ,
  ip_address        INET,
  user_agent        TEXT,

  CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- インデックス設計
CREATE INDEX idx_sessions_tenant_user
  ON sessions (tenant_id, user_id)
  WHERE revoked_at IS NULL;

CREATE INDEX idx_sessions_refresh_token
  ON sessions (refresh_token_hash)
  WHERE revoked_at IS NULL;

-- Row-Level Security
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON sessions
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

#### キャッシュ層: Redis

アクセストークンの有効性確認を高速化する。

```
キー設計:
  session:{tenant_id}:{session_id} → {有効=1, 無効=0}
  TTL = アクセストークンの有効期限 + バッファ (10分)

無効化時:
  SET session:{tenant_id}:{session_id} 0 EX 600
  -- 既存の発行済みアクセストークンが期限切れになるまで
  -- 無効フラグをキャッシュに保持する
```

この設計により、管理者による即時無効化でもRedisへの書き込み一回でスケールアウト全サーバーに即時反映される。

### 2.3 認証フロー

#### リクエスト認証 (低レイテンシ要件への対応)

```
1. リクエストヘッダからアクセストークン(JWT)を取得
2. JWTの署名検証 (公開鍵、サーバーローカル) → ~0.1ms
3. JWTのexp検証 → メモリ内処理
4. Redis で session_id の有効性確認
   → HIT: ~0.5-1ms (Redis レイテンシ)
   → MISS: DBから読み込みキャッシュ設定 → ~5-10ms
5. tenant_id の一致検証 (JWTペイロードとリクエストパスの照合)
6. 認証完了
```

**想定レイテンシ**: 通常ケースで 1-2ms 以内

#### アクセストークンのリフレッシュ

```
1. クライアントがリフレッシュトークンを送信
2. Redis でリフレッシュトークンのブロックリスト確認
3. DBでセッション検索 (refresh_token_hash で照合)
4. revoked_at が NULL であることを確認
5. 新しいアクセストークン(JWT)を発行
6. last_active_at を更新
7. 新しいアクセストークンを返却
```

### 2.4 即時セッション無効化 (管理者操作)

```
管理者操作: 特定ユーザーの全セッション無効化
  1. DB: sessions テーブルで該当 (tenant_id, user_id) の
         revoked_at を現在時刻に更新 (バッチ UPDATE)
  2. Redis: 該当セッション全ての無効フラグを設定
            session:{tenant_id}:{session_id} = 0 (TTL付き)
  3. 管理者に完了通知

管理者操作: 特定セッション(端末)の無効化
  1. DB: 特定 session_id の revoked_at を更新
  2. Redis: session:{tenant_id}:{session_id} = 0 を設定
```

**即時性の保証**: Redisへの書き込みが完了した時点で、以降の全認証リクエストで無効と判定される。既に発行済みのJWT(アクセストークン)は最大5分間有効だが、Redis確認ステップで無効判定されるため実質即時無効化となる。

---

## 3. スケーリング設計

### 3.1 ステートレスAPIサーバー

各APIサーバーはセッション状態を保持しない。

```
[クライアント]
     ↓ HTTPS
[ロードバランサー] (任意のサーバーにルーティング可能)
     ↓
[APIサーバー x N] (ステートレス、スケールアウト自由)
     ↓
[Redis Cluster]  ←→  [PostgreSQL (Primary + Replica)]
```

### 3.2 Redis のスケーリング

Redis Cluster による水平分散。シャーディングキーは `{tenant_id}:{session_id}` とする。

大規模テナントの場合、テナント専用のRedisクラスターを割り当てる運用も可能（テナント分離の強化）。

### 3.3 データベースのスケーリング

- **Read Replica**: セッション検索のread負荷をレプリカに分散
- **接続プーリング**: PgBouncer によるコネクション効率化
- **パーティショニング**: tenant_id によるテーブルパーティショニング（テナント数が多い場合）

---

## 4. セキュリティ設計

### 4.1 トークン保管

- **アクセストークン**: クライアントのメモリのみ (httpOnlyクッキーまたはメモリ変数、localStorageは禁止)
- **リフレッシュトークン**: httpOnly, Secure, SameSite=Strict クッキー

### 4.2 テナント境界の強制

JWTペイロードの `tenant_id` とリクエストパスの `tenant_id` を必ず照合する。ミドルウェア層で強制し、アプリケーション層に依存しない設計とする。

### 4.3 監査ログ

セッション関連の全操作を記録する。

```
AuditLog {
  event_type:   Enum (login, logout, token_refresh, session_revoked, ...)
  tenant_id:    UUID
  actor_id:     UUID   -- 操作者 (管理者または本人)
  target_user_id: UUID
  session_id:   UUID
  ip_address:   INET
  timestamp:    TIMESTAMPTZ
  metadata:     JSONB
}
```

---

## 5. 端末管理UI (管理者向け)

管理者が視覚的にセッションを管理できる機能を提供する。

```
GET /api/tenants/{tenant_id}/users/{user_id}/sessions

レスポンス例:
[
  {
    "session_id": "...",
    "device_name": "Chrome on MacBook Pro",
    "ip_address": "203.0.113.1",
    "created_at": "2026-02-20T09:00:00Z",
    "last_active_at": "2026-02-22T14:30:00Z",
    "is_current": false
  },
  ...
]

DELETE /api/tenants/{tenant_id}/sessions/{session_id}
  → 特定セッションの即時無効化

DELETE /api/tenants/{tenant_id}/users/{user_id}/sessions
  → 全セッションの即時無効化
```

---

## 6. 設計判断のまとめ

| 要件 | 採用アプローチ | 根拠 |
|------|--------------|------|
| 複数端末同時ログイン | セッションエンティティを端末単位で管理 | user_idではなくsession_idで識別 |
| 即時セッション無効化 | Redis無効フラグ + DB更新の二段階 | 全サーバーへの即時反映 |
| 水平スケーリング | ステートレスAPIサーバー + Redis Cluster | セッション状態をサーバー外部化 |
| 低レイテンシ認証 | 短命JWT (署名検証ローカル) + Redisキャッシュ | DB参照を最小化 |
| マルチテナント分離 | tenant_id のミドルウェア強制 + RLS | アプリ層のミスを防ぐ多層防御 |

### 想定レイテンシ実績値

- **通常認証**: 1-2ms (JWT検証 + Redis HIT)
- **キャッシュミス時**: 5-15ms (DB参照含む)
- **セッション無効化反映**: 即時 (次リクエスト時にRedisで検出)
- **リフレッシュトークン更新**: 10-20ms (DB read + write)

---

## 7. 実装上の注意点

### 7.1 クロックスキュー対策

分散環境では各サーバーの時刻が僅かにずれる。JWTのexp検証時に ±5秒のleewayを許容する設定を忘れない。

### 7.2 リフレッシュトークンのローテーション

リフレッシュトークンを使用するたびに新しいトークンを発行し、古いトークンを無効化する（リフレッシュトークンローテーション）。これにより盗まれたリフレッシュトークンの検出が可能になる。

### 7.3 同時リフレッシュリクエストの排他制御

複数タブから同時にトークンリフレッシュが来た場合のrace conditionを防ぐため、Redisの分散ロックを使用する。

```
LOCK session:{session_id}:refresh_lock (TTL=5秒)
  → 取得成功: リフレッシュ処理実行
  → 取得失敗: 短時間待機後リトライ or 409 Conflict
```

### 7.4 段階的移行

既存システムからの移行は、新旧セッション管理を並行稼働させながら段階的にトラフィックを切り替える方式（Blue-Green またはカナリアリリース）を推奨する。
