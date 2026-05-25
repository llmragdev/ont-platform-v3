# Phase 5 Week 9: ?먮룞 ?뺣젹 ?붿쭊 UI
## Codex (Frontend) ?섑뻾 吏?쒖꽌

**湲곌컙**: 2026-07-22 ~ 2026-07-26 (5??  
**?좊떦**: 80% (二쇰떦 24-30?쒓컙)  
**紐⑺몴**: LLM 湲곕컲 ?먮룞 留ㅽ븨 異붿쿇 UI 諛??좊ː???쒓컖??
---

## 媛쒖슂

Phase 4?먯꽌 援ъ텞???섎룞 留ㅽ븨 湲곕뒫??湲곕컲?쇰줈, **LLM(Claude API) 湲곕컲 ?먮룞 留ㅽ븨 ?붿쭊??異붿쿇 寃곌낵瑜??ъ슜?먭? 寃?졖룹듅?명븯??UI**瑜?援ы쁽?⑸땲??

### Week 9??3媛吏 ?듭떖 湲곕뒫

1. **?먮룞 留ㅽ븨 異붿쿇** (Task 9-1): LLM???앹꽦??留ㅽ븨 異붿쿇???쒓컖?곸쑝濡??쒖떆?섍퀬 ?좊ː???쒖떆
2. **?쇨큵 ?곸슜 & ?좏깮??寃??* (Task 9-2): 異붿쿇??留ㅽ븨??1-?대┃?쇰줈 ?쇨큵 ?곸슜?섍굅??媛쒕퀎 寃??3. **留ㅽ븨 ?뺤떊???쒓컖??* (Task 9-3): ?좊ː??遺꾪룷, 異붿쿇 洹쇨굅(evidence), ????쒖떆

---

## ?뵩 ?섍꼍 ?ㅼ젙 (?꾩닔)

```bash
# Conda ?섍꼍 ?쒖꽦??conda activate claud_fe

# ?묒뾽 ?붾젆?좊━
cd E:\ontology_edu\X_ont_std\ont_platform\v4\frontend

# ?섏〈???ㅼ튂
npm install

# 媛쒕컻 ?쒕쾭 ?쒖옉
npm run dev  # ?ы듃 3002

# ?뚯뒪??npm test
npm run cypress:open
```

---

## Task 9-1: ?먮룞 留ㅽ븨 異붿쿇 UI

**湲곌컙**: 07-22 ~ 07-23 (1.5??

### 紐⑺몴

LLM???앹꽦??留ㅽ븨 異붿쿇???쒓컖?곸쑝濡??쒖떆

### 援ы쁽 ??ぉ

#### 1) ?먮룞 留ㅽ븨 異붿쿇 ?뚯씠釉?```typescript
// src/components/AutomaticMappingPanel.tsx
import React, { useState, useEffect } from 'react';
import { Table, Tag, Rate, Tooltip, Button, Empty } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { useApi } from '@/hooks/useApi';

interface AutoMapping {
  id: string;
  externalUri: string;
  externalLabel: string;
  suggestedInternalId: string;
  suggestedInternalLabel: string;
  relationshipType: string;
  confidence: number; // 0.0 ~ 1.0
  evidence: string[]; // 留ㅽ븨 洹쇨굅
  alternatives?: Array<{
    internalId: string;
    internalLabel: string;
    confidence: number;
  }>;
  status: 'pending' | 'approved' | 'rejected' | 'manual_review';
}

export const AutomaticMappingPanel: React.FC<{
  importJobId: string;
  onUpdate?: (mappings: AutoMapping[]) => void;
}> = ({ importJobId, onUpdate }) => {
  const [mappings, setMappings] = useState<AutoMapping[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const { get, post } = useApi();

  // ?먮룞 留ㅽ븨 異붿쿇 濡쒕뱶
  useEffect(() => {
    loadAutoMappings();
  }, [importJobId]);

  const loadAutoMappings = async () => {
    setLoading(true);
    try {
      const response = await get(`/api/ontology/auto-mappings/${importJobId}`);
      setMappings(response.mappings);
    } finally {
      setLoading(false);
    }
  };

  // 留ㅽ븨 ?뱀씤
  const handleApprove = async (mappingId: string) => {
    await post(`/api/ontology/mappings/${mappingId}/approve`, {});
    setMappings(prev => prev.map(m =>
      m.id === mappingId ? { ...m, status: 'approved' } : m
    ));
  };

  // 留ㅽ븨 嫄곗젅
  const handleReject = async (mappingId: string) => {
    await post(`/api/ontology/mappings/${mappingId}/reject`, {});
    setMappings(prev => prev.map(m =>
      m.id === mappingId ? { ...m, status: 'rejected' } : m
    ));
  };

  // ?섎룞 寃???꾩슂
  const handleManualReview = async (mappingId: string) => {
    await post(`/api/ontology/mappings/${mappingId}/mark-review`, {});
    setMappings(prev => prev.map(m =>
      m.id === mappingId ? { ...m, status: 'manual_review' } : m
    ));
  };

  // ?좊ː???됱긽
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return '#52c41a'; // green
    if (confidence >= 0.7) return '#faad14'; // orange
    return '#ff4d4f'; // red
  };

  const getConfidenceText = (confidence: number) => {
    if (confidence >= 0.9) return '留ㅼ슦 ?믪쓬';
    if (confidence >= 0.7) return '?믪쓬';
    if (confidence >= 0.5) return '以묎컙';
    return '??쓬';
  };

  const columns = [
    {
      title: '?몃? 由ъ냼??,
      dataIndex: 'externalLabel',
      key: 'externalLabel',
      width: 150,
      render: (label: string, record: AutoMapping) => (
        <div>
          <p style={{ fontWeight: 'bold' }}>{label}</p>
          <code style={{ fontSize: '10px' }}>{record.externalUri}</code>
        </div>
      )
    },
    {
      title: '異붿쿇 ?대? ?뷀떚??,
      dataIndex: 'suggestedInternalLabel',
      key: 'suggestedInternalLabel',
      width: 150,
      render: (label: string, record: AutoMapping) => (
        <div>
          <p style={{ fontWeight: 'bold' }}>{label}</p>
          <code style={{ fontSize: '10px' }}>{record.suggestedInternalId}</code>
        </div>
      )
    },
    {
      title: '愿怨?,
      dataIndex: 'relationshipType',
      key: 'relationshipType',
      width: 120,
      render: (type: string) => <Tag color="blue">{type}</Tag>
    },
    {
      title: '?좊ː??,
      dataIndex: 'confidence',
      key: 'confidence',
      width: 120,
      render: (confidence: number, record: AutoMapping) => (
        <Tooltip title={`${(confidence * 100).toFixed(1)}% - ${getConfidenceText(confidence)}`}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <div style={{
              width: 60,
              height: 8,
              backgroundColor: '#f0f0f0',
              borderRadius: 4,
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${confidence * 100}%`,
                height: '100%',
                backgroundColor: getConfidenceColor(confidence)
              }} />
            </div>
            <span>{(confidence * 100).toFixed(0)}%</span>
          </div>
        </Tooltip>
      )
    },
    {
      title: '洹쇨굅',
      dataIndex: 'evidence',
      key: 'evidence',
      width: 200,
      render: (evidence: string[]) => (
        <div>
          {evidence.slice(0, 2).map((e, idx) => (
            <div key={idx} style={{ fontSize: '12px', color: '#666' }}>??{e}</div>
          ))}
          {evidence.length > 2 && (
            <div style={{ fontSize: '12px', color: '#999' }}>... +{evidence.length - 2}媛?/div>
          )}
        </div>
      )
    },
    {
      title: '?곹깭',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap = {
          pending: <Tag color="blue">?湲?/Tag>,
          approved: <Tag color="green">?뱀씤??/Tag>,
          rejected: <Tag color="red">嫄곗젅??/Tag>,
          manual_review: <Tag color="orange">寃???꾩슂</Tag>
        };
        return statusMap[status] || <Tag>{status}</Tag>;
      }
    },
    {
      title: '?묒뾽',
      key: 'action',
      width: 150,
      render: (_, record: AutoMapping) => (
        <div style={{ display: 'flex', gap: 8 }}>
          {record.status === 'pending' ? (
            <>
              <Tooltip title="?뱀씤">
                <Button
                  size="small"
                  type="primary"
                  icon={<CheckCircleOutlined />}
                  onClick={() => handleApprove(record.id)}
                />
              </Tooltip>
              <Tooltip title="嫄곗젅">
                <Button
                  size="small"
                  danger
                  icon={<CloseCircleOutlined />}
                  onClick={() => handleReject(record.id)}
                />
              </Tooltip>
              <Tooltip title="?섎룞 寃??>
                <Button
                  size="small"
                  icon={<QuestionCircleOutlined />}
                  onClick={() => handleManualReview(record.id)}
                />
              </Tooltip>
            </>
          ) : null}
        </div>
      )
    }
  ];

  const statistics = {
    total: mappings.length,
    approved: mappings.filter(m => m.status === 'approved').length,
    rejected: mappings.filter(m => m.status === 'rejected').length,
    pending: mappings.filter(m => m.status === 'pending').length,
    manualReview: mappings.filter(m => m.status === 'manual_review').length
  };

  return (
    <div className="auto-mapping-panel">
      {/* ?듦퀎 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: 16,
        marginBottom: 24
      }}>
        <div style={{ padding: 12, backgroundColor: '#f0f0f0', borderRadius: 4 }}>
          <div style={{ fontSize: '12px', color: '#666' }}>?꾩껜</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{statistics.total}</div>
        </div>
        <div style={{ padding: 12, backgroundColor: '#f6ffed', borderRadius: 4 }}>
          <div style={{ fontSize: '12px', color: '#666' }}>?뱀씤??/div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
            {statistics.approved}
          </div>
        </div>
        <div style={{ padding: 12, backgroundColor: '#fff1f0', borderRadius: 4 }}>
          <div style={{ fontSize: '12px', color: '#666' }}>嫄곗젅??/div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff4d4f' }}>
            {statistics.rejected}
          </div>
        </div>
        <div style={{ padding: 12, backgroundColor: '#fffbe6', borderRadius: 4 }}>
          <div style={{ fontSize: '12px', color: '#666' }}>?湲?以?/div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
            {statistics.pending}
          </div>
        </div>
        <div style={{ padding: 12, backgroundColor: '#fef3c7', borderRadius: 4 }}>
          <div style={{ fontSize: '12px', color: '#666' }}>寃???꾩슂</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
            {statistics.manualReview}
          </div>
        </div>
      </div>

      {/* ?뚯씠釉?*/}
      {mappings.length === 0 ? (
        <Empty description="?먮룞 異붿쿇 留ㅽ븨 ?놁쓬" />
      ) : (
        <Table
          columns={columns}
          dataSource={mappings}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20, total: mappings.length }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys
          }}
        />
      )}
    </div>
  );
};
```

### ?깃났 湲곗? (Task 9-1)
- [ ] ?먮룞 留ㅽ븨 ?뚯씠釉? ?몃?, 異붿쿇 ?대?, 愿怨? ?좊ː?? 洹쇨굅, ?곹깭 ?쒖떆
- [ ] ?좊ː???쒓컖?? 吏꾪뻾??諛?+ ?쇱꽱??+ ?띿뒪???덉씠釉?- [ ] 洹쇨굅 ?쒖떆: ?곸쐞 2媛?洹쇨굅 + "+n媛? 異뺤빟 ?쒖떆
- [ ] ?듦퀎: ?꾩껜, ?뱀씤, 嫄곗젅, ?湲? 寃???꾩슂 ???쒖떆

---

## Task 9-2: ?쇨큵 ?곸슜 & ?좏깮??寃??
**湲곌컙**: 07-23 ~ 07-24 (1.5??

### 紐⑺몴

?좊ː?꾧? ?믪? 異붿쿇? 1-?대┃?쇰줈 ?쇨큵 ?곸슜, ??? 寃껋? 媛쒕퀎 寃??
### 援ы쁽 ??ぉ

#### 1) ?쇨큵 ?묒뾽 UI
```typescript
// src/components/BulkMappingActions.tsx
export const BulkMappingActions: React.FC<{
  selectedCount: number;
  confidenceThreshold: number;
  onApplyAll: () => Promise<void>;
  onApplyAboveThreshold: (threshold: number) => Promise<void>;
}> = ({ selectedCount, confidenceThreshold, onApplyAll, onApplyAboveThreshold }) => {
  const [loading, setLoading] = useState(false);

  const handleApplyAll = async () => {
    setLoading(true);
    try {
      await onApplyAll();
      message.success('紐⑤뱺 留ㅽ븨???뱀씤?섏뿀?듬땲??);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFiltered = async () => {
    setLoading(true);
    try {
      await onApplyAboveThreshold(confidenceThreshold);
      message.success(`?좊ː??${(confidenceThreshold * 100).toFixed(0)}% ?댁긽??留ㅽ븨???뱀씤?섏뿀?듬땲??);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
      <Button
        type="primary"
        onClick={handleApplyAll}
        loading={loading}
        disabled={selectedCount === 0}
      >
        ?좏깮??{selectedCount}媛?留ㅽ븨 ?쇨큵 ?뱀씤
      </Button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>?좊ː??/span>
        <Slider
          style={{ width: 200 }}
          min={0}
          max={100}
          step={5}
          value={confidenceThreshold * 100}
          onChange={(val) => {/* ... */}}
          marks={{ 0: '0%', 50: '50%', 80: '80%', 100: '100%' }}
        />
        <span>{(confidenceThreshold * 100).toFixed(0)}%</span>
      </div>

      <Button
        onClick={handleApplyFiltered}
        loading={loading}
      >
        ?좊ː??{(confidenceThreshold * 100).toFixed(0)}% ?댁긽 ?곸슜
      </Button>
    </div>
  );
};
```

#### 2) ?좏깮??寃???뚰겕?뚮줈??```typescript
// src/pages/MappingReviewPage.tsx
export const MappingReviewPage: React.FC = () => {
  const [mappings, setMappings] = useState<AutoMapping[]>([]);
  const [currentMappingIndex, setCurrentMappingIndex] = useState(0);
  const [userReviews, setUserReviews] = useState<Record<string, boolean>>({});

  const currentMapping = mappings[currentMappingIndex];

  const handleApprove = () => {
    setUserReviews(prev => ({
      ...prev,
      [currentMapping.id]: true
    }));
    setCurrentMappingIndex(prev => prev + 1);
  };

  const handleReject = () => {
    setUserReviews(prev => ({
      ...prev,
      [currentMapping.id]: false
    }));
    setCurrentMappingIndex(prev => prev + 1);
  };

  if (currentMappingIndex >= mappings.length) {
    return <div>??紐⑤뱺 留ㅽ븨 寃???꾨즺</div>;
  }

  return (
    <div className="review-page">
      <h2>留ㅽ븨 寃??({currentMappingIndex + 1} / {mappings.length})</h2>

      <Card>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          {/* ?몃? 由ъ냼??*/}
          <div>
            <h3>?몃? 由ъ냼??/h3>
            <p><strong>{currentMapping.externalLabel}</strong></p>
            <p><code>{currentMapping.externalUri}</code></p>
          </div>

          {/* 異붿쿇 ?대? ?뷀떚??*/}
          <div>
            <h3>異붿쿇 ?대? ?뷀떚??/h3>
            <p><strong>{currentMapping.suggestedInternalLabel}</strong></p>
            <p><code>{currentMapping.suggestedInternalId}</code></p>
          </div>
        </div>

        {/* 洹쇨굅 */}
        <div style={{ marginTop: 24 }}>
          <h3>留ㅽ븨 洹쇨굅</h3>
          <ul>
            {currentMapping.evidence.map((e, idx) => (
              <li key={idx}>{e}</li>
            ))}
          </ul>
        </div>

        {/* ???*/}
        {currentMapping.alternatives && currentMapping.alternatives.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <h3>?ㅻⅨ ???/h3>
            <Table
              columns={[
                { title: '?쇰꺼', dataIndex: 'internalLabel' },
                { title: '?좊ː??, dataIndex: 'confidence', render: (c) => `${(c * 100).toFixed(0)}%` }
              ]}
              dataSource={currentMapping.alternatives}
              pagination={false}
            />
          </div>
        )}

        {/* ?≪뀡 */}
        <div style={{ marginTop: 24, display: 'flex', gap: 16 }}>
          <Button type="primary" size="large" onClick={handleApprove}>
            ???뱀씤
          </Button>
          <Button danger size="large" onClick={handleReject}>
            ??嫄곗젅
          </Button>
        </div>
      </Card>
    </div>
  );
};
```

### ?깃났 湲곗? (Task 9-2)
- [ ] ?쇨큵 ?뱀씤: ?좏깮??留ㅽ븨 ?쇨큵 ?뱀씤
- [ ] ?좊ː???꾪꽣: ?щ씪?대뜑濡??꾧퀎媛??ㅼ젙 ???먮룞 ?곸슜
- [ ] ?좏깮??寃?? "寃???꾩슂" 留ㅽ븨留?媛쒕퀎 寃??- [ ] 吏꾪뻾 ?곹솴: 寃??吏꾪뻾瑜??쒖떆 (?꾩옱/?꾩껜)

---

## Task 9-3: 留ㅽ븨 ?뺤떊???쒓컖??
**湲곌컙**: 07-24 ~ 07-26 (2??

### 紐⑺몴

留ㅽ븨???좊ː??遺꾪룷, 異붿쿇 洹쇨굅, ??덉쓣 ?쒓컖?곸쑝濡??쒗쁽

### 援ы쁽 ??ぉ

#### 1) ?좊ː??遺꾪룷 李⑦듃
```typescript
// src/components/ConfidenceDistributionChart.tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export const ConfidenceDistributionChart: React.FC<{
  mappings: AutoMapping[];
}> = ({ mappings }) => {
  const distribution = [
    {
      range: '0-20%',
      count: mappings.filter(m => m.confidence < 0.2).length
    },
    {
      range: '20-40%',
      count: mappings.filter(m => m.confidence >= 0.2 && m.confidence < 0.4).length
    },
    {
      range: '40-60%',
      count: mappings.filter(m => m.confidence >= 0.4 && m.confidence < 0.6).length
    },
    {
      range: '60-80%',
      count: mappings.filter(m => m.confidence >= 0.6 && m.confidence < 0.8).length
    },
    {
      range: '80-100%',
      count: mappings.filter(m => m.confidence >= 0.8).length
    }
  ];

  return (
    <BarChart width={600} height={300} data={distribution}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="range" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="count" fill="#8884d8" />
    </BarChart>
  );
};
```

#### 2) 異붿쿇 洹쇨굅 ?쒓컖??```typescript
// src/components/EvidenceVisualization.tsx
export const EvidenceVisualization: React.FC<{
  mapping: AutoMapping;
}> = ({ mapping }) => {
  const evidenceScores = mapping.evidence.map((e, idx) => ({
    evidence: e,
    weight: (1 - idx * 0.15) // 泥?洹쇨굅媛 ??以묒슂
  }));

  return (
    <div className="evidence-viz">
      <h3>留ㅽ븨 洹쇨굅 遺꾩꽍</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {evidenceScores.map((e, idx) => (
          <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 200, height: 24, backgroundColor: '#f0f0f0', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{
                width: `${e.weight * 100}%`,
                height: '100%',
                backgroundColor: '#1890ff'
              }} />
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ margin: 0, fontSize: '12px' }}>{e.evidence}</p>
            </div>
            <span style={{ fontSize: '12px', color: '#666' }}>
              {(e.weight * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
```

#### 3) ???鍮꾧탳 UI
```typescript
// src/components/MappingAlternativesComparison.tsx
export const MappingAlternativesComparison: React.FC<{
  suggested: AutoMapping;
}> = ({ suggested }) => {
  const all = [
    {
      label: suggested.suggestedInternalLabel,
      id: suggested.suggestedInternalId,
      confidence: suggested.confidence,
      selected: true
    },
    ...(suggested.alternatives || [])
  ];

  return (
    <div>
      <h3>?곸쐞 留ㅽ븨 ?꾨낫</h3>
      <Table
        columns={[
          {
            title: '?쒖쐞',
            key: 'rank',
            render: (_, __, index) => index + 1
          },
          {
            title: '?쇰꺼',
            dataIndex: 'label',
            key: 'label'
          },
          {
            title: '?좊ː??,
            dataIndex: 'confidence',
            key: 'confidence',
            render: (c) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 100,
                  height: 8,
                  backgroundColor: '#f0f0f0',
                  borderRadius: 4,
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${c * 100}%`,
                    height: '100%',
                    backgroundColor: c >= 0.8 ? '#52c41a' : c >= 0.5 ? '#faad14' : '#ff4d4f'
                  }} />
                </div>
                <span>{(c * 100).toFixed(0)}%</span>
              </div>
            )
          },
          {
            title: '?곹깭',
            key: 'status',
            render: (_, record) => record.selected ? <Tag color="blue">?좏깮??/Tag> : null
          }
        ]}
        dataSource={all}
        pagination={false}
      />
    </div>
  );
};
```

### ?깃났 湲곗? (Task 9-3)
- [ ] ?좊ː??遺꾪룷 李⑦듃: 5媛?援ш컙蹂?留ㅽ븨 ???쒖떆
- [ ] 洹쇨굅 ?쒓컖?? 洹쇨굅蹂?媛以묒튂 諛?李⑦듃
- [ ] ???鍮꾧탳: ?곸쐞 3~5媛??꾨낫 ?좊ː??鍮꾧탳
- [ ] ?좏깮??留ㅽ븨 媛뺤“: ?꾩옱 ?좏깮??留ㅽ븨 ?쒓컖??媛뺤“

---

## ?렞 ?꾩껜 ?깃났 湲곗? (Week 9)

### UI/UX 紐⑺몴
- [ ] ?먮룞 留ㅽ븨 ?뚯씠釉? ?좊ː?? 洹쇨굅, ?곹깭 ?꾩쟾 ?쒖떆
- [ ] ?쇨큵 ?묒뾽: ?좊ː???꾪꽣濡??좏깮???곸슜
- [ ] ?쒓컖?? 遺꾪룷, 洹쇨굅, ???紐⑤몢 ?쒖떆

### 湲곕뒫 紐⑺몴
- [ ] ?먮룞 異붿쿇 濡쒕뱶: `/api/ontology/auto-mappings/{jobId}`
- [ ] 留ㅽ븨 ?뱀씤/嫄곗젅: 媛쒕퀎 + ?쇨큵 紐⑤몢 吏??- [ ] ?좊ː??湲곕컲 ?꾪꽣留? ?꾧퀎媛??ㅼ젙 ???먮룞 ?곸슜

### ?깅뒫 紐⑺몴
- [ ] ?먮룞 留ㅽ븨 濡쒕뱶: < 2珥?(1000媛?留ㅽ븨)
- [ ] UI ?뚮뜑留? < 500ms
- [ ] ?뚯씠釉??ㅽ겕濡? 遺?쒕윭???곹샇?묒슜

---

## ?뱥 蹂닿퀬?????吏??
**???寃쎈줈**: `task_logs/codex/YYYYMMDD_HHMM_PHASE5_WEEK9_Codex_Complete.md`

**?덉떆**: `20260726_1830_PHASE5_WEEK9_Codex_Complete.md`

**蹂닿퀬????ぉ**:
1. Task 9-1: ?먮룞 留ㅽ븨 異붿쿇 UI ?꾩꽦??2. Task 9-2: ?쇨큵 ?곸슜 湲곕뒫 (?좊ː???꾪꽣, ?좏깮??寃??
3. Task 9-3: ?좊ː???쒓컖??(遺꾪룷, 洹쇨굅, ???
4. ?ъ슜???쇰뱶諛?諛?媛쒖꽑 ?쒖븞

**?꾨즺 ??*: Claude媛 3媛?蹂닿퀬?쒕? 痍⑦빀?섏뿬 ?듯빀 蹂닿퀬?쒕? ?묒꽦?⑸땲??

