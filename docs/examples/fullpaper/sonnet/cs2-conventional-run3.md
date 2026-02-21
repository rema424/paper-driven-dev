# CS2 条件A: Conventional — マルチテナントSaaSセッション管理 (Run 3)

> **Run**: CS2-A-Run3
> **Date**: 2026-02-22
> **Model**: Claude Sonnet 4.6
> **Context**: Fresh agent invocation

---

# マルチテナントSaaSセッション管理システムの設計分析

## 問題の整理と制約分析

### 要件間のトレードオフ

まず、4つの要件が生み出すテンションを明確にする。

| 要件 | 技術的意味 | 他要件との衝突 |
|------|-----------|--------------|
| 複数端末からの同時ログイン | セッションが1対多の関係 | セッション無効化の範囲を複雑化 |
| 即時無効化 | リアルタイム状態変更の伝播 | レイテンシ最小化と競合 |
| 水平スケーリング | 状態をサーバー外部に持つ | ローカルキャッシュの整合性を困難に |
| レイテンシ最小化 | キャッシュや署名検証を活用 | 即時無効化と根本的に対立 |

特に「即時無効化」と「レイテンシ最小化」は本質的にトレードオフの関係にある。JWTのような自己完結型トークンはレイテンシを低くできるが、失効の伝播に遅延が生じる。逆にすべてのリクエストでデータベースを参照すれば即時性は得られるがレイテンシが上がる。

---

## アーキテクチャ設計

### データモデル

マルチテナントとマルチデバイスを考慮したセッション構造を定義する。

```
Tenant (テナント)
  └── User (ユーザー)
        └── Session[] (セッション、端末ごとに1つ)
              ├── session_id      (UUID v4)
              ├── tenant_id       (テナント識別子)
              ├── user_id         (ユーザー識別子)
              ├── device_id       (端末識別子)
              ├── created_at      (作成日時)
              ├── last_active_at  (最終アクティビティ)
              ├── expires_at      (有効期限)
              ├── revoked         (無効化フラグ)
              ├── revoked_at      (無効化日時)
              └── metadata        (IPアドレス、UserAgent等)
```

セッションとトークンを分離することがポイントである。セッションはサーバー側の状態として永続化し、クライアントが持つトークンはセッションへの参照に過ぎない。

### トークン戦略: 参照トークン + Redis キャッシュ

純粋なJWTではなく、参照トークン（Opaque Token）とサーバー側キャッシュを組み合わせる。

```
クライアント              APIサーバー              Redis            PostgreSQL
    |                       |                       |                   |
    |--- リクエスト(token) -->|                       |                   |
    |                       |-- GET session:token -->|                   |
    |                       |<-- セッションデータ ---|                   |
    |                       |  (ヒット時はDBアクセス不要)                |
    |                       |                       |                   |
    |                       | (キャッシュミス時のみ) |                   |
    |                       |------- SELECT session WHERE token=? ------>|
    |                       |<------ セッションデータ ------------------|
    |                       |-- SET session:token (TTL) -->|             |
    |<-- レスポンス ---------|                       |                   |
```

**トークン形式**: `{tenant_id}.{session_id}.{random_bytes}` を base64url エンコードしたもの。テナントIDをプレフィックスとして含めることで、ルーティングやシャーディングに活用できる。

### Redisキャッシュの設計

```
キー: session:{token_hash}
値: {
  session_id: "...",
  user_id: "...",
  tenant_id: "...",
  permissions: [...],
  revoked: false,
  expires_at: 1740000000
}
TTL: 300秒（5分）
```

TTLを短く設定することで、無効化の最大遅延を制御する。TTL=300秒なら、管理者がセッションを無効化してから最大5分以内には確実に拒否される。これは多くのSaaSで許容範囲内である。

### 即時無効化の実装

管理者による無効化を即時に反映するための機構を追加する。

**方法1: Redis キャッシュの直接削除**

```
管理者操作              APIサーバー(管理)         Redis          PostgreSQL
    |                       |                       |                  |
    |-- セッション無効化 -->|                       |                  |
    |                       |-- UPDATE session SET revoked=true ------->|
    |                       |-- DEL session:{token_hash} -->|           |
    |<-- 完了 --------------|                       |                   |
```

Redisのキャッシュを削除することで、次回のリクエスト時にDBから再取得させ、revoked=trueを検知できる。

**方法2: ブロックリストの併用**

無効化されたセッションIDをRedisのSetに格納する。

```
キー: revoked_sessions:{tenant_id}
値: Set{session_id_1, session_id_2, ...}
TTL: セッション最大有効期限と同じ
```

認証フローに追加チェックを挟む。

```python
def authenticate(token: str) -> Session | None:
    # 1. トークンからセッション情報を取得（Redisキャッシュ優先）
    session = get_session_from_cache_or_db(token)
    if session is None:
        return None

    # 2. ブロックリストを確認（Redisのインメモリ操作なのでレイテンシ小）
    if is_revoked(session.tenant_id, session.session_id):
        return None

    # 3. 有効期限チェック
    if session.expires_at < now():
        return None

    return session
```

ブロックリストへの追加はO(1)で、確認もO(1)のRedis SISMEMBER操作であり、レイテンシへの影響は最小限。

### 水平スケーリングへの対応

APIサーバーはステートレスに設計し、状態はすべてRedisとPostgreSQLに集中させる。

```
          ロードバランサー
         /       |        \
    API-1      API-2      API-3
         \       |        /
          Redis Cluster
              |
          PostgreSQL
         (Primary/Replica)
```

**Redis Cluster の設計**:
- テナントIDをシャーディングキーとして使用
- `{tenant_id}:session:{token_hash}` のようなキー設計でテナントごとにデータを局所化
- Redis Clusterの場合、同じハッシュタグ `{tenant_id}` を持つキーは同一スロットに配置される

**PostgreSQL の設計**:
- テナントIDによるパーティショニング（Range または Hash）
- `sessions` テーブルを `tenant_id` でパーティション分割
- 読み取りはレプリカにオフロード

---

## セキュリティ設計

### テナント分離

すべての操作でテナントIDを検証する。

```python
def get_session(token: str, claimed_tenant_id: str) -> Session | None:
    session = _get_session_internal(token)
    if session is None:
        return None

    # テナントIDの一致を検証（テナント越境攻撃の防止）
    if session.tenant_id != claimed_tenant_id:
        return None

    return session
```

### トークンのローテーション

長期間同じトークンを使い続けるリスクを軽減するため、一定期間ごとにトークンをローテーションする。

```
リクエスト処理時に last_active_at から X時間経過していたら:
1. 新しいトークンを生成
2. DBとRedisを新トークンで更新
3. レスポンスヘッダーに新トークンを返す
4. クライアントは新トークンを保存して以降使用する
```

---

## 運用設計

### セッション一覧・管理API

```
GET  /admin/tenants/{tenant_id}/users/{user_id}/sessions
     → ユーザーの全アクティブセッション一覧

DELETE /admin/tenants/{tenant_id}/users/{user_id}/sessions/{session_id}
     → 特定セッションの即時無効化

DELETE /admin/tenants/{tenant_id}/users/{user_id}/sessions
     → ユーザーの全セッションを一括無効化

DELETE /admin/tenants/{tenant_id}/sessions
     → テナント全体のセッションを無効化（テナント停止時等）
```

### 期限切れセッションのクリーンアップ

```sql
-- バックグラウンドジョブで定期実行
DELETE FROM sessions
WHERE expires_at < NOW() - INTERVAL '1 day'
  AND revoked = true;
```

---

## レイテンシ目標とトレードオフの整理

| ケース | レイテンシ | 説明 |
|--------|-----------|------|
| Redisキャッシュヒット | ~1ms | 最も多いケース |
| キャッシュミス（DB参照） | ~10ms | 初回アクセスや障害後 |
| 無効化後・初回リクエスト | ~10ms | DBから再取得が必要 |
| 無効化の最大伝播遅延 | ≤ TTL(300秒) | 許容範囲の設計判断 |

TTLを短くすれば無効化の即時性が上がるが、Redisへの負荷とDB参照頻度が増す。本設計ではTTL=300秒を起点とし、要件に応じて調整することを推奨する。即時無効化が厳格に求められる場合（例：セキュリティインシデント）は、ブロックリスト方式を優先し、TTLを無効化の補完手段と位置づける。

---

## 実装上の注意点

1. **トークンはハッシュ化して保存**: Redisのキーとして使うトークンは SHA-256 でハッシュ化し、生のトークンを永続化しない。
2. **タイミング攻撃への対策**: トークンの比較は定数時間比較（`hmac.compare_digest`相当）を使用する。
3. **監査ログ**: セッション作成・無効化イベントをすべて記録し、コンプライアンス対応と障害調査に備える。
4. **グレースフルシャットダウン**: APIサーバーの停止時にインフライトリクエストの処理が完了するまで待機する設計を採用し、セッション状態の不整合を防ぐ。
