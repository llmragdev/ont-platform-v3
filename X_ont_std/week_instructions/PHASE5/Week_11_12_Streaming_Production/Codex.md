# Phase 5 Week 11-12: ?댁쁺 ??쒕낫??& 紐⑤땲?곕쭅
## Codex (Frontend) ?섑뻾 吏?쒖꽌

**湲곌컙**: 2026-08-05 ~ 2026-08-16 (2二?  
**?좊떦**: 90% (二쇰떦 27-30?쒓컙)  
**紐⑺몴**: ?꾨줈?뺤뀡 ?댁쁺 ??쒕낫?? 留ㅽ븨 踰꾩쟾 愿由?UI, ?ㅼ떆媛?紐⑤땲?곕쭅

---

## 媛쒖슂

?쒖뒪?쒖씠 ?꾨줈?뺤뀡 ?섍꼍??吏꾩엯?섎㈃???댁쁺?怨??곗씠???붿??덉뼱瑜??꾪븳 **?댁쁺 ??쒕낫??*媛 ?꾩닔?낅땲?? Codex???ㅼ쓬???대떦?⑸땲??

1. **留ㅽ븨 踰꾩쟾 愿由?UI**: 踰꾩쟾 ?덉뒪?좊━, 鍮꾧탳, 濡ㅻ갚
2. **?ㅼ떆媛?紐⑤땲?곕쭅 ??쒕낫??*: 泥섎━?? 吏?곗떆媛? ?먮윭??3. **SLA 紐⑤땲?곕쭅**: 紐⑺몴 ?ъ꽦???쒓컖??
---

## Task 11-1: 留ㅽ븨 踰꾩쟾 愿由?UI

**湲곌컙**: 08-05 ~ 08-08 (2??

### 援ы쁽 ??ぉ

```typescript
// src/components/MappingVersionControl.tsx
import React, { useState, useEffect } from 'react';

interface MappingVersion {
  versionId: string;
  tag: string;
  description: string;
  mappingCount: number;
  createdAt: string;
  createdBy: string;
  status: 'stable' | 'draft' | 'deprecated';
}

export const MappingVersionControl: React.FC = () => {
  const [versions, setVersions] = useState<MappingVersion[]>([]);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [diffResult, setDiffResult] = useState(null);

  useEffect(() => {
    loadVersions();
  }, []);

  const loadVersions = async () => {
    const response = await fetch('/api/ontology/mapping-versions');
    const data = await response.json();
    setVersions(data.versions.sort((a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    ));
  };

  const handleRollback = async (versionId: string) => {
    // v4 ?섍꼍: antd Modal.confirm ????먯껜 confirm dialog ?먮뒗 window.confirm ?ъ슜
    const confirmed = window.confirm(
      `??踰꾩쟾?쇰줈 濡ㅻ갚?섏떆寃좎뒿?덇퉴? (?꾩옱 留ㅽ븨??蹂寃쎈맗?덈떎)`
    );
    
    if (!confirmed) return;
    
    const response = await fetch(
      `/api/ontology/mapping-versions/${versionId}/rollback`,
      { method: 'POST' }
    );
    const result = await response.json();
    
    if (result.success) {
      alert('濡ㅻ갚 ?꾨즺');  // ?먮뒗 toast notification ?ъ슜
      loadVersions();
    } else {
      alert('濡ㅻ갚 ?ㅽ뙣');
    }
  };

  const handleCompare = async () => {
    if (selectedVersions.length !== 2) {
      alert('鍮꾧탳??踰꾩쟾 2媛쒕? ?좏깮?섏꽭??);  // v4: antd message ???alert ?먮뒗 toast
      return;
    }

    const response = await fetch('/api/ontology/mapping-versions/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        version1Id: selectedVersions[0],
        version2Id: selectedVersions[1]
      })
    });

    const result = await response.json();
    setDiffResult(result);
    setComparisonMode(true);
  };

  return (
    <div className="version-control-page">
      {/* ??꾨씪??*/}
      <div style={{ marginBottom: 32 }}>
        <h2>留ㅽ븨 踰꾩쟾 ?덉뒪?좊━</h2>
        <Timeline>
          {versions.map((version) => (
            <Timeline.Item
              key={version.versionId}
              dot={
                <div style={{
                  width: 16,
                  height: 16,
                  backgroundColor: version.status === 'stable' ? '#52c41a' : '#faad14',
                  borderRadius: '50%'
                }} />
              }
            >
              <div style={{ padding: '12px 0' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div>
                    <strong style={{ fontSize: '16px' }}>{version.tag}</strong>
                    <Tag
                      color={
                        version.status === 'stable' ? 'green' :
                        version.status === 'draft' ? 'orange' : 'red'
                      }
                      style={{ marginLeft: 8 }}
                    >
                      {version.status}
                    </Tag>
                  </div>
                  <span style={{ color: '#999' }}>
                    {new Date(version.createdAt).toLocaleString()}
                  </span>
                  <span style={{ color: '#999' }}>
                    by {version.createdBy}
                  </span>
                </div>
                <p>{version.description}</p>
                <p style={{ fontSize: '12px', color: '#666' }}>
                  留ㅽ븨 媛쒖닔: {version.mappingCount}
                </p>
                <Space>
                  <Button
                    size="small"
                    onClick={() => handleRollback(version.versionId)}
                    icon={<RollbackOutlined />}
                  >
                    Rollback
                  </Button>
                  <Button
                    size="small"
                    type={selectedVersions.includes(version.versionId) ? 'primary' : 'default'}
                    onClick={() => {
                      setSelectedVersions(prev =>
                        prev.includes(version.versionId)
                          ? prev.filter(id => id !== version.versionId)
                          : [...prev, version.versionId]
                      );
                    }}
                  >
                    {selectedVersions.includes(version.versionId) ? '?좏깮?? : '?좏깮'}
                  </Button>
                </Space>
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      </div>

      {/* 鍮꾧탳 */}
      {selectedVersions.length === 2 && (
        <Button
          type="primary"
          onClick={handleCompare}
          style={{ marginBottom: 16 }}
        >
          ?좏깮??2媛?踰꾩쟾 鍮꾧탳
        </Button>
      )}

      {comparisonMode && diffResult && (
        <div style={{
          padding: 16,
          backgroundColor: '#f5f5f5',
          borderRadius: 4,
          marginBottom: 32
        }}>
          <h3>踰꾩쟾 鍮꾧탳</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <h4>{diffResult.version1}</h4>
              <Table
                columns={[
                  { title: '異붽???, dataIndex: 'added' }
                ]}
                dataSource={diffResult.added.slice(0, 10)}
                pagination={false}
              />
            </div>
            <div>
              <h4>{diffResult.version2}</h4>
              <Table
                columns={[
                  { title: '?쒓굅??, dataIndex: 'removed' }
                ]}
                dataSource={diffResult.removed.slice(0, 10)}
                pagination={false}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## Task 11-2: ?ㅼ떆媛?紐⑤땲?곕쭅 ??쒕낫??
**湲곌컙**: 08-08 ~ 08-12 (2??

### 援ы쁽 ??ぉ

```typescript
// src/components/OperationsDashboard.tsx
import React, { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Statistic, Row, Col, Card, Gauge } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

export const OperationsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState(null);
  const [historyData, setHistoryData] = useState([]);

  useEffect(() => {
    const interval = setInterval(loadMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    const response = await fetch('/api/ontology/operational-metrics');
    const data = await response.json();
    setMetrics(data.currentMetrics);
    setHistoryData(prev => [...prev, data.currentMetrics].slice(-60)); // 理쒓렐 60媛?  };

  if (!metrics) return <div>濡쒕뵫 以?..</div>;

  return (
    <div className="operations-dashboard" style={{ padding: 24 }}>
      <h1>?⑦넧濡쒖? ?뺤옣 ?쒖뒪??- ?댁쁺 ??쒕낫??/h1>

      {/* ?듭떖 吏??*/}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="留ㅽ븨 泥섎━??
              value={metrics.mappingThroughput}
              suffix="mappings/sec"
              valueStyle={{ color: metrics.mappingThroughput > 100 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="荑쇰━ ?묐떟 (P95)"
              value={metrics.queryP95ResponseMs}
              suffix="ms"
              valueStyle={{ color: metrics.queryP95ResponseMs < 200 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="罹먯떆 ?덊듃??
              value={metrics.cacheHitRate * 100}
              suffix="%"
              precision={1}
              valueStyle={{ color: metrics.cacheHitRate > 0.7 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="?먮윭??
              value={metrics.errorRate * 100}
              suffix="%"
              precision={2}
              valueStyle={{ color: metrics.errorRate < 0.05 ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* ?쒓퀎??李⑦듃 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="泥섎━??異붿씠">
            <LineChart width={500} height={300} data={historyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="mappingThroughput" stroke="#8884d8" />
            </LineChart>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="?묐떟 ?쒓컙 異붿씠">
            <LineChart width={500} height={300} data={historyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="queryP95ResponseMs" stroke="#ff4d4f" />
            </LineChart>
          </Card>
        </Col>
      </Row>

      {/* SLA 以?섎룄 */}
      <Card title="SLA 以?? style={{ marginTop: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Gauge
              value={metrics.mappingAccuracy * 100}
              percent={metrics.mappingAccuracy}
              text="留ㅽ븨 ?뺥솗??
              type="dashboard"
            />
          </Col>
          <Col span={8}>
            <Gauge
              value={metrics.systemAvailability * 100}
              percent={metrics.systemAvailability}
              text="媛?⑹꽦"
              type="dashboard"
            />
          </Col>
          <Col span={8}>
            <Gauge
              value={metrics.slaComplianceRate * 100}
              percent={metrics.slaComplianceRate}
              text="SLA 以??
              type="dashboard"
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
};
```

---

## Task 11-3: ?뚮┝ 諛??먮룞 ???
**湲곌컙**: 08-12 ~ 08-16 (2??

### 援ы쁽 ??ぉ

```typescript
// src/components/AlertsPanel.tsx
export const AlertsPanel: React.FC = () => {
  const [alerts, setAlerts] = useState([]);

  // WebSocket?쇰줈 ?ㅼ떆媛??뚮┝ ?섏떊
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8001/alerts');
    
    ws.onmessage = (event) => {
      const alert = JSON.parse(event.data);
      setAlerts(prev => [alert, ...prev].slice(0, 100));
    };
    
    return () => ws.close();
  }, []);

  return (
    <div className="alerts-panel">
      <h3>?쒖뒪???뚮┝</h3>
      {alerts.map((alert, idx) => (
        <div
          key={idx}
          style={{
            padding: 12,
            marginBottom: 8,
            borderLeft: `3px solid ${
              alert.severity === 'critical' ? '#ff4d4f' :
              alert.severity === 'warning' ? '#faad14' :
              '#1890ff'
            }`,
            backgroundColor: '#f5f5f5'
          }}
        >
          <div style={{ fontWeight: 'bold' }}>
            {alert.title}
          </div>
          <div style={{ fontSize: '12px', color: '#666', marginTop: 4 }}>
            {alert.message}
          </div>
          <div style={{ fontSize: '10px', color: '#999', marginTop: 4 }}>
            {new Date(alert.timestamp).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## API ?붽뎄?ы빆

```
GET /api/ontology/mapping-versions
GET /api/ontology/operational-metrics
POST /api/ontology/mapping-versions/{versionId}/rollback
POST /api/ontology/mapping-versions/compare
WS /alerts (WebSocket)
```

---

**理쒖쥌 寃利?*: 紐⑤뱺 ?댁쁺 湲곕뒫 寃利?諛??꾨줈?뺤뀡 以鍮??꾨즺

