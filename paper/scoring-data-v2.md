# Scoring Data v2 — 著者1次採点

> **Date**: 2026-02-20
> **Scorer**: 著者（CC 支援による一貫適用）
> **Rubric**: Protocol v1 §5（ルーブリック v2）
> **Scope**: 40件全出力（4条件 × 2CS × 5Run）

---

## Summary Table

### CS1: RAG ストリーミング引用リナンバリング

| Run | A: Conventional ||| B: Paper Format ||| C: PDD Template ||| D: Checklist |||
|-----|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|     | CR | TP | TL | CR | TP | TL | CR | TP | TL | CR | TP | TL |
| 1   | 0  | 0  | 32 | 0  | 2  | 54 | 3  | 4  | 127| 3  | 5  |102 |
| 2   | 0  | 0  | 40 | 0  | 2  | 60 | 3  | 5  | 117| 3  | 4  | 89 |
| 3   | 0  | 0  | 33 | 0  | 2  | 63 | 3  | 5  | 125| 4  | 6  | 62 |
| 4   | 0  | 2  | 56 | 0  | 2  | 71 | 3  | 6  | 86 | 3  | 5  | 71 |
| 5   | 0  | 0  | 52 | 0  | 2  | 48 | 3  | 6  | 114| 4  | 5  | 95 |
| **Mean** | **0.0** | **0.4** | **42.6** | **0.0** | **2.0** | **59.2** | **3.0** | **5.2** | **113.8** | **3.4** | **5.0** | **83.8** |

### CS2: マルチテナント SaaS セッション管理

| Run | A: Conventional ||| B: Paper Format ||| C: PDD Template ||| D: Checklist |||
|-----|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|     | CR | TP | TL | CR | TP | TL | CR | TP | TL | CR | TP | TL |
| 1   | 1  | 0  | 33 | 1  | 3  |101 | 4  | 5  | 106| 4  | 5  |106 |
| 2   | 0  | 0  | 35 | 1  | 2  | 72 | 3  | 5  | 82 | 4  | 5  | 52 |
| 3   | 1  | 0  | 33 | 1  | 2  | 77 | 3  | 5  | 101| 4  | 6  | 82 |
| 4   | 0  | 0  | 36 | 1  | 2  | 68 | 4  | 6  | 95 | 4  | 6  | 54 |
| 5   | 1  | 0  | 39 | 1  | 1  | 71 | 3  | 5  | 100| 4  | 6  | 68 |
| **Mean** | **0.6** | **0.0** | **35.2** | **1.0** | **2.0** | **77.8** | **3.4** | **5.2** | **96.8** | **4.0** | **5.6** | **72.4** |

### Co-primary 指標の条件別集計（両CS統合）

| Condition | CR mean (SD) | TP mean (SD) |
|-----------|-------------|-------------|
| A: Conventional | 0.30 (0.48) | 0.20 (0.63) |
| B: Paper Format | 0.50 (0.53) | 2.00 (0.47) |
| C: PDD Template | 3.20 (0.42) | 5.20 (0.63) |
| D: Checklist | 3.70 (0.48) | 5.30 (0.67) |

### Full Indicator Summary（全指標）

| File | CR | TP | CD | EA | FI | TL |
|------|---:|---:|---:|---:|---:|---:|
| CS1-A-Run1 | 0 | 0 | 3 | 3 | 0 | 32 |
| CS1-A-Run2 | 0 | 0 | 4 | 0 | 0 | 40 |
| CS1-A-Run3 | 0 | 0 | 3 | 0 | 0 | 33 |
| CS1-A-Run4 | 0 | 2 | 3 | 2 | 0 | 56 |
| CS1-A-Run5 | 0 | 0 | 3 | 0 | 0 | 52 |
| CS1-B-Run1 | 0 | 2 | 4 | 0 | 0 | 54 |
| CS1-B-Run2 | 0 | 2 | 4 | 2 | 0 | 60 |
| CS1-B-Run3 | 0 | 2 | 3 | 0 | 1 | 63 |
| CS1-B-Run4 | 0 | 2 | 4 | 0 | 1 | 71 |
| CS1-B-Run5 | 0 | 2 | 3 | 0 | 0 | 48 |
| CS1-C-Run1 | 3 | 4 | 5 | 4 | 0 | 127 |
| CS1-C-Run2 | 3 | 5 | 3 | 4 | 1 | 117 |
| CS1-C-Run3 | 3 | 5 | 4 | 3 | 0 | 125 |
| CS1-C-Run4 | 3 | 6 | 3 | 3 | 0 | 86 |
| CS1-C-Run5 | 3 | 6 | 4 | 3 | 0 | 114 |
| CS1-D-Run1 | 3 | 5 | 4 | 5 | 0 | 102 |
| CS1-D-Run2 | 3 | 4 | 3 | 3 | 0 | 89 |
| CS1-D-Run3 | 4 | 6 | 3 | 4 | 0 | 62 |
| CS1-D-Run4 | 3 | 5 | 3 | 3 | 0 | 71 |
| CS1-D-Run5 | 4 | 5 | 4 | 2 | 0 | 95 |
| CS2-A-Run1 | 1 | 0 | 0 | 2 | 0 | 33 |
| CS2-A-Run2 | 0 | 0 | 0 | 0 | 0 | 35 |
| CS2-A-Run3 | 1 | 0 | 0 | 0 | 0 | 33 |
| CS2-A-Run4 | 0 | 0 | 2 | 0 | 0 | 36 |
| CS2-A-Run5 | 1 | 0 | 1 | 0 | 0 | 39 |
| CS2-B-Run1 | 1 | 3 | 2 | 1 | 0 | 101 |
| CS2-B-Run2 | 1 | 2 | 1 | 2 | 1 | 72 |
| CS2-B-Run3 | 1 | 2 | 2 | 2 | 1 | 77 |
| CS2-B-Run4 | 1 | 2 | 1 | 2 | 1 | 68 |
| CS2-B-Run5 | 1 | 1 | 2 | 1 | 2 | 71 |
| CS2-C-Run1 | 4 | 5 | 5 | 4 | 0 | 106 |
| CS2-C-Run2 | 3 | 5 | 3 | 3 | 1 | 82 |
| CS2-C-Run3 | 3 | 5 | 4 | 3 | 0 | 101 |
| CS2-C-Run4 | 4 | 6 | 4 | 3 | 1 | 95 |
| CS2-C-Run5 | 3 | 5 | 4 | 3 | 0 | 100 |
| CS2-D-Run1 | 4 | 5 | 4 | 5 | 0 | 106 |
| CS2-D-Run2 | 4 | 5 | 3 | 4 | 0 | 52 |
| CS2-D-Run3 | 4 | 6 | 3 | 3 | 0 | 82 |
| CS2-D-Run4 | 4 | 6 | 3 | 4 | 0 | 54 |
| CS2-D-Run5 | 4 | 6 | 3 | 4 | 0 | 68 |

**凡例**: CR = Conflicting requirements, TP = Testable properties, CD = Constraints disclosed, EA = Existing approaches, FI = Formal invariants, TL = Total lines

---

## Detailed Scoring

### CS1-A-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 0 | none |
| Constraints disclosed | 3 | Token boundary marker splitting requires buffer; invalid source_id handling needed; multiple citation normalization policy required |
| Existing approaches | 3 | Pre-numbering by retrieval rank (番号が飛ぶ); post-processing after completion (リアルタイム要件違反); re-numbering with diff (番号不変に反する) |
| Formal invariants | 0 | none |
| Total lines | 32 | — |

### CS1-A-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 0 | none |
| Constraints disclosed | 4 | Chunk splitting requires incremental parser; invalid ID returns [?]; concurrency requires mutex/atomic; reconnection requires persisting citation_map per message_id |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 40 | — |

### CS1-A-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 0 | none |
| Constraints disclosed | 3 | Numbering granularity must be decided (chunk_id vs document_id); only permitted source_ids accepted; reconnection requires persisting state per response_id |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 33 | — |

### CS1-A-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 2 | "id_to_num は一度入れたら変更しない" (map immutability); "next_num は増えるだけ" (monotonic counter) |
| Constraints disclosed | 3 | Citations must be machine-readable tags not free text; invalid source_id shown as [?] with monitoring; numbering scope per-response not per-conversation |
| Existing approaches | 2 | Post-processing batch numbering ("実装が簡単" but "要件違反"); pre-fixed by retrieval rank ("番号は絶対に変わらない" but "連番性が弱い") |
| Formal invariants | 0 | none |
| Total lines | 56 | — |

### CS1-A-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 0 | none |
| Constraints disclosed | 3 | Chunk boundary splits tags (buffer + state machine needed); LLM may produce non-existent source_id (ignore + log); re-numbering to remove gaps forbidden |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 52 | — |

### CS1-B-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 2 | R2 proof: "Mは追記のみの単調増加写像であり発行済み番号を再代入しない" (immutable map); R3 proof: "本文内の[n]は必ずM由来であり一覧もMから生成" (single source of truth) |
| Constraints disclosed | 4 | Marker split across token boundaries; unknown key validation; LLM direct [1] output must be suppressed; text-delta vs citation-event channel tradeoff |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 54 | — |

### CS1-B-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 2 | 命題2: "id2numは追記のみで更新し既存キーの値を変更しない" (append-only immutability); 命題3: "num2id[1..next_num-1]から生成すれば本文内番号と一対一対応" (same-source consistency) |
| Constraints disclosed | 4 | Append-only stream assumption (rollback needs extra layer); partial token requires parser buffer; invalid IDs logged or displayed per policy; session persistence of id2num for reconnection |
| Existing approaches | 2 | Post-processing batch numbering ("実装容易だがR2違反"); pre-fixed by retrieval rank ("不変だが可読性が低い") |
| Formal invariants | 0 | none |
| Total lines | 60 | — |

### CS1-B-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 2 | "M[s]は未定義→定義済みへの一度だけの遷移で更新操作を禁止" (one-way state transition); "同一状態M/Lから生成されるため参照先不一致が起きない" (single-source consistency) |
| Constraints disclosed | 3 | LLM must output structured citation tokens; single serialization point for numbering; post-stream text modifications must not re-number |
| Existing approaches | 0 | none |
| Formal invariants | 1 | Formal mapping definition: f:R→N, event set E={e_t}, citation set C_t⊆R |
| Total lines | 63 | — |

### CS1-B-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 2 | 命題1: "M[c]は未登録時のみ代入され上書き操作が存在しない" (write-once immutability); 命題3: "同一写像Mを唯一の真実源として参照する" (single source of truth) |
| Constraints disclosed | 4 | Session-level M persistence for reconnection; source_id validation mandatory; UI must separate text/bibliography rendering; LLM retry must reuse same M |
| Existing approaches | 0 | none |
| Formal invariants | 1 | B[k] = meta(M^{-1}(k)) formal bibliography definition |
| Total lines | 71 | — |

### CS1-B-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none |
| Testable properties | 2 | 命題1: "sid_to_idxは初回挿入のみで更新されるため表示済み番号は不変" (insert-once immutability); 命題3: "同一状態から生成されるため必ず一致" (same-state consistency) |
| Constraints disclosed | 3 | Citation order fixed by token arrival order; multi-chunk same-document unified via canonicalize; unknown ID outputs [?] with audit log |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 48 | — |

### CS1-C-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "低遅延な逐次表示 vs 事後確定が必要な整形"; "番号の不変性 vs 生成の可変性"; "使用したものだけ列挙 vs 先に番号割当" |
| Testable properties | 4 | S6: 番号不変, 単調増加, 完了時一覧整合, 使用ソースのみ列挙 |
| Constraints disclosed | 5 | 推敲不可能; マーカー分割・誤生成リスク; 未知ID再生成戦略; UI/プロトコル設計トレードオフ; マルチターン整合 |
| Existing approaches | 4 | 事後整形, 取得順固定番号, 2パス生成, 初出時割当 |
| Formal invariants | 0 | none |
| Total lines | 127 | — |

### CS1-C-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "低遅延表示 vs 全文確定後の最適整形"; "表示済み番号の不変性 vs 生成過程の可塑性"; "連番の可読性 vs 内部IDの安定性" |
| Testable properties | 5 | S6: 初出割当の決定性, 番号不変性, 完了時整合性, チャンク分断耐性, 未登録IDの扱い |
| Constraints disclosed | 3 | LLMが構造化引用構文を守る前提; append-only配信で事後修正困難; 複数ターン番号継続戦略未解決 |
| Existing approaches | 4 | 事後一括リナンバリング, 検索順位事前固定, 仮番号表示後差替, 内部IDそのまま表示 |
| Formal invariants | 1 | M_t(id)=|dom(M_{t-1})|+1 の写像定義 |
| Total lines | 117 | — |

### CS1-C-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "リアルタイム表示 vs 最終最適化"; "番号不変性 vs 連番の見栄え"; "低遅延 vs 厳密整合検証" |
| Testable properties | 5 | S6: 初回採番の不変性, 再引用の再利用, 出現順連番, 完了時整合, 冪等性 |
| Constraints disclosed | 4 | 構造化引用イベント必要; 編集型ストリーム別途設計; 未検証引用UI方針; 分散環境順序保証 |
| Existing approaches | 3 | 事後採番, 検索順位固定採番, 可変再マッピング |
| Formal invariants | 0 | none |
| Total lines | 125 | — |

### CS1-C-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "低遅延表示 vs 最終確定性"; "番号不変性 vs 番号最適化"; "生成自由度 vs 引用整合性保証" |
| Testable properties | 6 | S6: map空+初出→[1]不変; 再出→[1]再利用; 新規初出→[2]+[1]不変; チャンク分断→単一番号; 再接続再送→同一番号収束; 完了→全件一致 |
| Constraints disclosed | 3 | 番号順は初出順で重要度順ではない; 不正source_idの自動修復は限定的; 長文で可読性低下 |
| Existing approaches | 3 | 事後一括番号付け, 検索順位事前固定番号, プレースホルダ表示後置換 |
| Formal invariants | 0 | none |
| Total lines | 86 | — |

### CS1-C-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "即時性 vs 確定性"; "可読な連番化 vs 不変性"; "厳密整合性 vs 低遅延" |
| Testable properties | 6 | S6: 初出採番, 再引用の不変性, 後続イベント非干渉, 完了時整合性, リアルタイム性(50ms以内), 不正ID遮断 |
| Constraints disclosed | 4 | 番号整合は保証するが意味的正しさは不保証; LLM自己修正時の冗長; マルチターン別設計; 構造化デコード等未解決 |
| Existing approaches | 3 | 後処理リナンバリング, 検索順位固定マッピング, 一時番号＋後方修正 |
| Formal invariants | 0 | none |
| Total lines | 114 | — |

### CS1-D-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "低遅延ストリーミング vs 確定後の最適な整形"; "番号の不変性 vs 後処理による修正"; "引用粒度 vs 可読性" |
| Testable properties | 5 | S8: 初出の付番, 再引用の安定性, 初出順の保証, ストリーム分割マーカー, 未知ID混入 |
| Constraints disclosed | 4 | LLMがマーカー規約を破ると崩壊; 不要引用の消去・統合不可; doc-level正規化粒度; モデル出力とシステム追記の区別 |
| Existing approaches | 5 | 事後付番, 検索結果固定番号, LLM自身に[n]管理, 2パス生成, 構造化引用イベント方式 |
| Formal invariants | 0 | none |
| Total lines | 102 | — |

### CS1-D-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "即時性 vs 正確性"; "番号不変 vs 見た目の最適化"; "モデル自由度 vs 実装堅牢性" |
| Testable properties | 4 | S8: 初出順+再引用の統合テスト, チャンク分割耐性, 未知ID扱い, 接続断→復旧後番号維持 |
| Constraints disclosed | 3 | モデルが正規引用フォーマットを守る前提; 番号不変優先で見た目最適化不可; 引用整合と意味的裏付けは別問題 |
| Existing approaches | 3 | 後処理一括採番, 検索結果事前採番, LLMに[n]直接生成. 5.4(推奨)は提案解法のため除外 |
| Formal invariants | 0 | none |
| Total lines | 89 | — |

### CS1-D-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "即時表示 vs 最終整合性"; "連番の可読性 vs 内部IDの厳密性"; "番号不変性 vs 訂正可能性"; "厳格検証 vs 低遅延" |
| Testable properties | 6 | S8: map空+source_3初出→[1]; source_3再出→[1]; source_7初出→[2]+[1]不変; チャンク分割→1回採番; 未取得ID→エラー記録; 完了→一覧と表示1対1一致 |
| Constraints disclosed | 3 | LLM引用タグ誤生成→参照欠落増; 番号不変要件で番号最適化不可; 複合引用・脚注標準化が必要 |
| Existing approaches | 4 | 完了後リナンバリング, 内部IDそのまま表示, 取得順事前固定番号, LLMに直接[1][2]生成 |
| Formal invariants | 0 | none |
| Total lines | 62 | — |

### CS1-D-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "即時表示 vs 正確性"; "番号不変 vs きれいな連番"; "実装単純性 vs 堅牢性" |
| Testable properties | 5 | S8: 初出順+再引用→表示+一覧一致; チャンク分割→バッファ→完成後1回表示; 未許可source_99→[?]+既存不変; 再送重複→採番不変; 正常終了→完全一致 |
| Constraints disclosed | 3 | LLM構造化タグ不遵守時バリデータ必須; 引用内容の正しさは別問題; 欠番風の見え方が起こり得る |
| Existing approaches | 3 | 後処理一括採番, 検索順位事前固定採番, 自然文から正規表現抽出 |
| Formal invariants | 0 | none |
| Total lines | 71 | — |

### CS1-D-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "即時性 vs 正確性"; "番号不変性 vs 最適な連番圧縮"; "実装単純性 vs 堅牢性"; "LLM自由出力 vs 厳格フォーマット" |
| Testable properties | 5 | S8: source_7→source_3順→[1]→[2]+一覧一致; source_7複数回→全て[1]; チャンク分割→完成時1回[1]; 未取得source_99→無効+非混入; 接続断→既存維持+新規のみ |
| Constraints disclosed | 4 | 後方編集ストリームと不変番号が衝突; 自由テキスト引用記法の抽出失敗リスク; 未知ID処理ポリシー明文化必要; 監視メトリクス(invalid_citation_rate等)追加必要 |
| Existing approaches | 2 | 完了後一括変換, 事前固定マップ. 5.3(推奨)は提案解法のため除外 |
| Formal invariants | 0 | none |
| Total lines | 95 | — |

### CS2-A-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | "低レイテンシ＝ステートレス寄り vs 即時無効化＝ステートフル寄り" |
| Testable properties | 0 | none |
| Constraints disclosed | 0 | none |
| Existing approaches | 2 | "完全ステートフル" (easy revocation but high latency); "完全ステートレス" (min latency but no immediate revocation) |
| Formal invariants | 0 | none |
| Total lines | 33 | — |

### CS2-A-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none — two problems listed casually but not formally framed as opposing pair |
| Testable properties | 0 | none |
| Constraints disclosed | 0 | none |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 35 | — |

### CS2-A-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | "要件の衝突点は、即時失効 と 低レイテンシ です" |
| Testable properties | 0 | none |
| Constraints disclosed | 0 | none |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 33 | — |

### CS2-A-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 0 | none — design goals listed but no explicitly named opposing pair |
| Testable properties | 0 | none |
| Constraints disclosed | 2 | Pub/Sub message loss requiring re-sync; Redis failure requiring fail-closed |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 36 | — |

### CS2-A-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | "低レイテンシはステートレスJWTが有利" vs "即時無効化は中央状態参照が必要" |
| Testable properties | 0 | none |
| Constraints disclosed | 1 | Event delivery delay triggers fallback to Redis strict mode |
| Existing approaches | 0 | none |
| Formal invariants | 0 | none |
| Total lines | 39 | — |

### CS2-B-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | Stateless tokens = low latency but hard to revoke vs shared state = immediate revocation but latency cost |
| Testable properties | 3 | Admin deletes sid set→next request fails; no stale internal-token window via per-request assertion; at most 1 store lookup per external request |
| Constraints disclosed | 2 | Unbounded worst-case revocation cost without session count limit; multi-region RTT degrades store lookup latency |
| Existing approaches | 1 | Self-contained tokens (long-lived JWT): need blacklist negating statelessness |
| Formal invariants | 0 | none |
| Total lines | 101 | — |

### CS2-B-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | Centralized auth server = good revocation but high latency vs self-contained tokens = low latency but hard to revoke |
| Testable properties | 2 | Old user_version tokens rejected after INCR; E[T]~0.18ms at p=0.99 from solution formula |
| Constraints disclosed | 1 | Network partition prevents theoretical perfect immediacy |
| Existing approaches | 2 | Centralized auth query (good revocation, high latency); self-contained token (low latency, hard revocation) |
| Formal invariants | 1 | E[T] = T_verify + p*T_cache + (1-p)*(T_cache+T_redis) with numerical evaluation |
| Total lines | 72 | — |

### CS2-B-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | "ステートレスJWT低遅延だが即時失効困難 vs 完全ステートフルDB照会は失効制御強いがレイテンシ不利" |
| Testable properties | 2 | Old epoch tokens rejected + refresh non-renewable after INCR+SET; guarantee scoped to "new requests after commit" |
| Constraints disclosed | 2 | In-flight requests cannot be stopped; event delay triggers KVS direct fallback |
| Existing approaches | 2 | Stateless JWT (low latency, hard revocation); full stateful DB query (strong revocation, latency penalty) |
| Formal invariants | 1 | E[L_auth] = L_sig + h*L_L1 + (1-h)*L_KVS |
| Total lines | 77 | — |

### CS2-B-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | "無状態化はスケールしやすいが即時失効難しい vs 完全状態管理は失効制御強いがI/O増加で遅延増" |
| Testable properties | 2 | Old user_version tokens immediately invalidated; D <= max(D_pubsub, TTL_L1) propagation delay bound |
| Constraints disclosed | 1 | Redis failure: high-privilege fail-closed, general fail-soft |
| Existing approaches | 2 | Stateless auth (scalable but hard to revoke); full state management (strong revocation but high latency) |
| Formal invariants | 1 | E[L] and D <= max(D_pubsub, TTL_L1) |
| Total lines | 68 | — |

### CS2-B-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 1 | "完全ステートレス認証は失効即時性とトレードオフを持つ" |
| Testable properties | 1 | Formal correctness proposition: monotonic user_version guarantees old tokens rejected, with proof sketch |
| Constraints disclosed | 2 | Event delivery failure causes latency degradation (fallback to Redis); multi-region replication delay |
| Existing approaches | 1 | Stateless auth (tradeoff with immediate revocation) |
| Formal invariants | 2 | E[L] formula; correctness proposition with monotonicity proof |
| Total lines | 71 | — |

### CS2-C-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "低レイテンシ vs 即時無効化"; "水平スケール vs 強制ログアウト"; "細粒度 vs 運用コスト"; "テナント分離 vs 実装複雑性" |
| Testable properties | 5 | S6: simultaneous session_ids; user_epoch increment causing rejection; selective sid revocation; new node cache-miss fallback; local epoch_cache + signature hot path |
| Constraints disclosed | 5 | SLO-based not instantaneous due to propagation; multi-region convergence time; tenant key management; DoS via cache-miss flooding; at-least-once delivery + stream replay |
| Existing approaches | 4 | Server-side session, stateless JWT, JWT+blacklist, OAuth2 introspection |
| Formal invariants | 0 | none |
| Total lines | 106 | — |

### CS2-C-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "低遅延認証 と 即時失効"; "複数端末同時ログイン と 不正利用時の被害最小化"; "水平スケーリング と 強整合な失効判定" |
| Testable properties | 5 | S6: dual session_id active; revocation_version causing 401 within SLA; scale-out matching results; L1 hit rate p99 target; tenant_id scoped revocation isolation |
| Constraints disclosed | 3 | SLA-based not strict simultaneous; Redis failure policy must be explicit; multi-region global ordering needed |
| Existing approaches | 3 | In-memory session, stateless JWT, central introspection |
| Formal invariants | 1 | accept = sig_valid ∧ not_expired ∧ session_active ∧ token_iat > revoked_after(user) |
| Total lines | 82 | — |

### CS2-C-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "即時失効性 vs 低レイテンシ"; "ステートレス性 vs 管理可能性"; "複数端末同時ログイン vs 攻撃面積最小化" |
| Testable properties | 5 | S6: independent sid authentication; user_epoch rejection; selective sid revocation; 2N scale-out correctness; L1 cache hit no-I/O completion |
| Constraints disclosed | 4 | SLO p99 < X ms definition needed; multi-region epoch consistency; event monitoring/re-sync/key rotation; load test and fault injection needed |
| Existing approaches | 3 | Centralized session store, stateless JWT, token introspection |
| Formal invariants | 0 | none |
| Total lines | 101 | — |

### CS2-C-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "即時失効と低レイテンシ"; "水平スケーリングとセッション一貫性"; "複数端末同時ログインと被害最小化"; "テナント分離と運用単純性" |
| Testable properties | 6 | S6: dual session_id; user_epoch SLO-bound rejection; selective session_id revocation; scale-out invariance; L1 cache p99 latency; tenant_id isolation |
| Constraints disclosed | 4 | Network partition theoretical limit; partition policy fail-open/fail-closed; event resend/ordering verification; hot-key mitigation for large tenant skew |
| Existing approaches | 3 | In-node stateful session, stateless JWT, central introspection |
| Formal invariants | 1 | valid = sig_ok ∧ not_expired ∧ token.user_epoch == current_user_epoch ∧ sid_not_revoked |
| Total lines | 95 | — |

### CS2-C-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 3 | "低レイテンシ認証 vs 即時失効"; "水平スケーリング vs 一貫した失効状態"; "複数端末同時ログイン許容 vs セキュリティ統制" |
| Testable properties | 5 | S6: independent session auth; invalidate(U) causing rejection within Delta; 3-to-30 scale-out consistency; local cache p99 single-digit ms; tenant-scoped revocation isolation |
| Constraints disclosed | 4 | Immediacy depends on propagation delay and clock skew; fault boundary for Event Bus/Redis partition; cross-region increases delay; formal verification and SLO quantification needed |
| Existing approaches | 3 | Centralized session store, stateless JWT, opaque token + introspection |
| Formal invariants | 0 | none |
| Total lines | 100 | — |

### CS2-D-Run1
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "低レイテンシ vs 即時失効"; "強い整合性 vs 可用性/運用容易性"; "長寿命 vs 短寿命アクセストークン"; "細粒度失効 vs 実装/データ量" |
| Testable properties | 5 | S8: session_version update causing A/B rejection; selective sidB revocation with sidA continuing; new node Redis warm-up then local verification; restart re-subscribe catching up; JWT+memory-only hot path |
| Constraints disclosed | 4 | Absolute instant revocation impractical, SLA needed; event infra quality critical; multi-region replication delay; security hardening incremental |
| Existing approaches | 5 | Server-side opaque+Redis, sticky session, stateless JWT, JWT+introspection, JWT+user version |
| Formal invariants | 0 | none |
| Total lines | 106 | — |

### CS2-D-Run2
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "低レイテンシ と 即時失効"; "強整合性 と 可用性/スケール"; "短命トークン と UX/負荷"; "テナント分離 と 運用簡素化" |
| Testable properties | 5 | S8: both terminals 200; all terminals 401 post-revocation; scale-out maintains auth rate and SLO; Redis delay with L1 hit p99; tenant-scoped revocation isolation |
| Constraints disclosed | 3 | Absolute instant impossible, SLO required; Redis/PubSub dependency requires re-sendable event infra; cross-region and automatic anomaly-based revocation |
| Existing approaches | 4 | Stateless JWT, server memory session, central store per-request, hybrid short-lived + central revocation |
| Formal invariants | 0 | none |
| Total lines | 52 | — |

### CS2-D-Run3
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "低レイテンシ vs 即時失効"; "ステートレス性 vs 制御性"; "長寿命トークン vs セキュリティ"; "強い整合性 vs 運用コスト" |
| Testable properties | 6 | S8: both terminals succeed with separate session_ids; all sessions rejected within 1 second post-epoch; selective session_id revocation; N+M scale-out consistency; p95 latency target; tenant-scoped revocation isolation |
| Constraints disclosed | 3 | Network fault creates short inconsistency window; Redis dependency requires fail-open/fail-closed policy; TTL risk window remains |
| Existing approaches | 3 | Stateless JWT, central session per-request, server memory sticky |
| Formal invariants | 0 | none |
| Total lines | 82 | — |

### CS2-D-Run4
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "即時無効化 vs 低レイテンシ"; "ステートレス性 vs 強制失効"; "複数端末許容 vs セキュリティ面積"; "テナント分離 vs 運用単純性" |
| Testable properties | 6 | S8: both terminals 200; all nodes 401 post-revocation; re-login with new epoch valid; new node reflects revocation; Redis delay with local cache safe-side; p95/p99 latency targets |
| Constraints disclosed | 3 | Redis/event infra as critical dependency; event loss requires re-sync mechanism; cross-region requires SLO-based definition |
| Existing approaches | 4 | Stateless JWT, RDB session per-request, Redis centralized session, hybrid short-lived + central revocation |
| Formal invariants | 0 | none |
| Total lines | 54 | — |

### CS2-D-Run5
| Indicator | Count | Evidence |
|-----------|------:|---------|
| Conflicting requirements | 4 | "即時無効化と低レイテンシ"; "ステートレス性と失効制御"; "長寿命トークンとセキュリティ"; "厳密なテナント分離と運用効率" |
| Testable properties | 6 | S8: both terminals 200 with independent sessions; all sessions 401 within 1 second; selective sid revocation A=401 B=200; 4→12→4 scale with SLO; p95/p99 with cache hit; cross-tenant revocation attempt rejected 403 |
| Constraints disclosed | 3 | "instant" is SLO-based not physical; event delay/partition leaves inconsistency window limited by TTL; multi-region propagation optimization needed |
| Existing approaches | 4 | Opaque session + Redis, stateless JWT, introspection API, hybrid short-lived + version |
| Formal invariants | 0 | none |
| Total lines | 68 | — |
