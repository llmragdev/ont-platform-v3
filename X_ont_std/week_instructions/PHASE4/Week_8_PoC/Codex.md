# Phase 4 Week 8: 온톨로지 확장 PoC E2E 검증
## Codex (Frontend) 수행 지시서

**기간**: 2026-07-15 ~ 2026-07-19 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 외부 온톨로지 확장 전체 파이프라인 E2E 검증 및 PoC 완성

---

## 개요

Week 7에서 구축한 온톨로지 확장 UI 기능들을 통합하여, **RDF 임포트 → 미리보기 → 매핑 → 그래프 반영 → SPARQL 검증**의 완전한 E2E 흐름을 구현하고 검증합니다.

### Week 8의 3가지 핵심 목표

1. **E2E 파이프라인 통합** (Task 8-1): 임포트부터 SPARQL 검증까지 일관된 흐름
2. **Schema Conflict 처리** (Task 8-2): 충돌 감지, 표시, 해결 방안 제시
3. **Provenance & 신뢰도 관리** (Task 8-3): 매핑 출처, 신뢰도, 승인 상태 노출

---

## 🔧 환경 설정 (필수)

```bash
# Conda 환경 활성화
conda activate claud_fe

# 작업 디렉토리
cd E:\ontology_edu\X_ont_std\ont_platform\v4\frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm run dev  # 포트 3001

# 코드 검증
npm run build  # TypeScript 컴파일 검증
npm run lint   # 코드 스타일 검증

# E2E 테스트
npm run cypress:run  # headless 모드
# npm run cypress:open  # (개발 중 대화형 모드, 선택)

```

---

## Task 8-1: E2E 파이프라인 통합

**기간**: 07-15 ~ 07-16 (1.5일)

### 목표

RDF 임포트부터 SPARQL 검증까지 일관된 사용자 경험 제공

### 구현 항목

#### 1) 온톨로지 확장 마법사 (Wizard)
```typescript
// src/components/OntologyExtensionWizard.tsx
import React, { useState } from 'react';
import { api } from '@/lib/api';

type WizardStep = 'upload' | 'preview' | 'mapping' | 'graph' | 'validation' | 'complete';

interface WizardState {
  file?: File;
  preview?: ImportPreview;
  selectedMappings?: MappingRule[];
  graphMergeResult?: {
    newNodes: number;
    newEdges: number;
    conflictsResolved: number;
  };
  validationResult?: {
    queriesRun: number;
    passed: number;
    failed: number;
  };
  importJobId?: string;
}

export const OntologyExtensionWizard: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<WizardStep>('upload');
  const [state, setState] = useState<WizardState>({});
  const [error, setError] = useState<string | null>(null);

  // Step 1: 파일 업로드
  const handleUpload = async (file: File) => {
    setState(prev => ({ ...prev, file }));
    setCurrentStep('preview');
  };

  // Step 2: Preview 확인
  const handlePreviewConfirm = async (preview: ImportPreview) => {
    setState(prev => ({ ...prev, preview }));
    setCurrentStep('mapping');
  };

  // Step 3: 매핑 검토 & 수정
  const handleMappingComplete = async (mappings: MappingRule[]) => {
    setState(prev => ({ ...prev, selectedMappings: mappings }));
    setCurrentStep('graph');
  };

  // Step 4: 그래프 병합
  const handleGraphMerge = async () => {
    try {
      const result = await api.post('/api/ontology/merge', {
        file: state.file,
        mappings: state.selectedMappings,
        previewId: state.preview?.fileInfo.name
      });

      setState(prev => ({
        ...prev,
        graphMergeResult: result,
        importJobId: result.jobId
      }));
      setCurrentStep('validation');
      // v4: toast notification 사용 (alert 대신)
      setError(null);
    } catch (err: any) {
      setError(`그래프 병합 실패: ${err.message}`);
    }
  };

  // Step 5: SPARQL 검증
  const handleValidation = async () => {
    try {
      const result = await api.post('/api/ontology/validate-sparql', {
        jobId: state.importJobId,
        queries: [
          'SELECT COUNT(*) WHERE { ?s ?p ?o . }',
          'SELECT DISTINCT ?type WHERE { ?s a ?type . }',
          'SELECT ?s WHERE { ?s a <http://schema.org/Person> . } LIMIT 10'
        ]
      });

      setState(prev => ({
        ...prev,
        validationResult: result
      }));
      setCurrentStep('complete');
      setError(null);
    } catch (err: any) {
      setError(`검증 실패: ${err.message}`);
    }
  };

  const stepLabels = {
    upload: '파일 업로드',
    preview: '미리보기',
    mapping: '매핑',
    graph: '그래프 병합',
    validation: '검증',
    complete: '완료'
  };

  const steps = ['upload', 'preview', 'mapping', 'graph', 'validation', 'complete'];
  const stepIndex = steps.indexOf(currentStep);

  // v4: Tailwind 기반 단계 표시
  const renderStepIndicator = () => (
    <div className="flex gap-2 mb-6">
      {steps.map((step, idx) => (
        <div key={step} className="flex items-center">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
            idx === stepIndex ? 'bg-blue-600 text-white' :
            idx < stepIndex ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'
          }`}>
            {idx + 1}
          </div>
          <span className="ml-2 text-sm">{stepLabels[step as WizardStep]}</span>
          {idx < steps.length - 1 && (
            <div className="ml-4 w-8 h-0.5 bg-gray-300" />
          )}
        </div>
      ))}
    </div>
  );

  return (
    <div className="wizard-container p-6">
      {renderStepIndicator()}
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
          {error}
        </div>
      )}
      
      <div className="mt-6">
        {currentStep === 'upload' && (
          <OntologyImportUI onUpload={handleUpload} />
        )}
        {currentStep === 'preview' && state.file && (
          <ImportPreviewDialog 
            file={state.file}
            onConfirm={handlePreviewConfirm}
          />
        )}
        {currentStep === 'mapping' && state.preview && (
          <MappingReviewPanel
            preview={state.preview}
            onComplete={handleMappingComplete}
          />
        )}
        {currentStep === 'graph' && (
          <div>
            {state.graphMergeResult ? (
              <div>
                <p className="text-green-600 font-bold">✅ 병합 완료</p>
                <ul className="list-disc pl-6 mt-2">
                  <li>새 노드: {state.graphMergeResult.newNodes}</li>
                  <li>새 엣지: {state.graphMergeResult.newEdges}</li>
                  <li>해결된 충돌: {state.graphMergeResult.conflictsResolved}</li>
                </ul>
                <button 
                  onClick={() => setCurrentStep('validation')}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
                >
                  다음
                </button>
              </div>
            ) : (
              <button 
                onClick={handleGraphMerge}
                className="px-6 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
              >
                그래프 병합 실행
              </button>
            )}
          </div>
        )}
        {currentStep === 'validation' && (
          <div>
            {state.validationResult ? (
              <div>
                <p className="font-bold mb-2">검증 결과:</p>
                <ul className="list-disc pl-6">
                  <li>실행된 쿼리: {state.validationResult.queriesRun}</li>
                  <li>성공: {state.validationResult.passed}</li>
                  <li>실패: {state.validationResult.failed}</li>
                </ul>
                <button 
                  onClick={() => setCurrentStep('complete')}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
                >
                  완료
                </button>
              </div>
            ) : (
              <button 
                onClick={handleValidation}
                className="px-6 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
              >
                검증 실행
              </button>
            )}
          </div>
        )}
        {currentStep === 'complete' && (
          <div className="text-center">
            <p className="text-xl font-bold text-green-600 mb-2">✅ 온톨로지 확장이 완료되었습니다!</p>
            <p className="text-gray-600 mb-4">Import Job ID: {state.importJobId}</p>
            <a href="/ontology-explorer" className="px-6 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700 inline-block">
              그래프 탐색
            </a>
          </div>
        )}
      </div>
    </div>
  );
};
```

#### 2) E2E Cypress 테스트
```typescript
// cypress/e2e/ontology-extension-e2e.cy.ts
describe('온톨로지 확장 E2E', () => {
  beforeEach(() => {
    cy.visit('http://localhost:3001/ontology-extension');
  });

  it('전체 파이프라인: 임포트 → 미리보기 → 매핑 → 병합 → 검증', () => {
    // Step 1: 파일 업로드
    cy.get('input[type="file"]').selectFile('cypress/fixtures/test-ontology.rdf');
    cy.get('button:contains("다음")').click();

    // Step 2: 미리보기 확인
    cy.get('[data-testid="preview-stats"]').should('be.visible');
    cy.contains('추가될 클래스').should('exist');
    cy.get('button:contains("다음")').click();

    // Step 3: 매핑 검토
    cy.get('[data-testid="mapping-table"]').should('be.visible');
    cy.get('button:contains("다음")').click();

    // Step 4: 그래프 병합
    cy.get('button:contains("그래프 병합 실행")').click();
    cy.contains('병합 완료').should('exist');

    // Step 5: SPARQL 검증
    cy.get('button:contains("검증 실행")').click();
    cy.contains('성공').should('exist');
  });

  it('충돌이 있는 RDF 임포트', () => {
    cy.get('input[type="file"]').selectFile('cypress/fixtures/conflict-ontology.rdf');
    cy.get('button:contains("다음")').click();
    cy.get('button[data-testid="conflicts-tab"]').click();
    cy.get('[data-testid="conflict-list"]').should('have.length.greaterThan', 0);
  });
});
```

### 성공 기준 (Task 8-1)
- [ ] 6단계 마법사: 업로드 → 미리보기 → 매핑 → 병합 → 검증 → 완료
- [ ] 각 단계 간 상태 전달: 다음 단계에서 이전 데이터 사용 가능
- [ ] E2E 테스트: 5+ 시나리오 (성공, 충돌, 오류 등)
- [ ] 완료 시간: < 10초 (1M 트리플 기준)

---

## Task 8-2: Schema Conflict 처리

**기간**: 07-16 ~ 07-18 (2일)

### 목표

스키마 충돌을 감지하고 사용자가 해결 방안을 선택할 수 있게 함

### 구현 항목

#### 1) 충돌 감지 & 표시
```typescript
// src/components/SchemaConflictResolver.tsx
interface SchemaConflict {
  id: string;
  type: 'label_conflict' | 'uri_conflict' | 'property_conflict' | 'range_conflict' | 'domain_conflict';
  external: {
    uri: string;
    label: string;
    class?: string;
  };
  internal: {
    uri: string;
    label: string;
    class?: string;
  };
  resolutionOptions: Array<{
    id: string;
    label: string;
    description: string;
    recommended: boolean;
  }>;
  selectedResolution?: string;
}

export const SchemaConflictResolver: React.FC<{
  conflicts: SchemaConflict[];
  onResolve: (conflicts: SchemaConflict[]) => Promise<void>;
}> = ({ conflicts, onResolve }) => {
  const [conflictList, setConflictList] = useState(conflicts);
  const [loading, setLoading] = useState(false);

  const handleResolutionChange = (conflictId: string, resolution: string) => {
    setConflictList(prev =>
      prev.map(c =>
        c.id === conflictId ? { ...c, selectedResolution: resolution } : c
      )
    );
  };

  const handleSave = async () => {
    if (conflictList.some(c => !c.selectedResolution)) {
      alert('모든 충돌을 해결해주세요');
      return;
    }

    setLoading(true);
    try {
      await onResolve(conflictList);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* v4: antd Alert → Tailwind 기반 경고 박스 */}
      <div className="mb-4 p-4 bg-yellow-100 border border-yellow-400 rounded text-yellow-700">
        ⚠️ {conflictList.length}개의 스키마 충돌이 감지되었습니다
      </div>
      
      {/* v4: antd Table → Tailwind 기반 표 자체 구현 */}
      <div className="overflow-x-auto mb-4">
        <table className="w-full border-collapse border border-gray-300">
          <thead className="bg-gray-100">
            <tr>
              <th className="border p-2 text-left">타입</th>
              <th className="border p-2 text-left">외부</th>
              <th className="border p-2 text-left">내부</th>
              <th className="border p-2 text-left">해결 방안</th>
            </tr>
          </thead>
          <tbody>
            {conflictList.map((conflict) => (
              <tr key={conflict.id} className="hover:bg-gray-50">
                <td className="border p-2">
                  <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                    {conflict.type}
                  </span>
                </td>
          {
            title: '외부',
            dataIndex: 'external',
            key: 'external',
            render: (external) => (
              <div>
                <p>{external.label}</p>
                <code style={{ fontSize: '10px' }}>{external.uri}</code>
              </div>
            )
          },
          {
            title: '내부',
            dataIndex: 'internal',
            key: 'internal',
            render: (internal) => (
              <div>
                <p>{internal.label}</p>
                <code style={{ fontSize: '10px' }}>{internal.uri}</code>
              </div>
            )
          },
          {
            title: '해결 방안',
            key: 'resolution',
            render: (_, record: SchemaConflict) => (
              <Select
                value={record.selectedResolution}
                onChange={(val) => handleResolutionChange(record.id, val)}
                style={{ width: '100%' }}
              >
                {record.resolutionOptions.map(opt => (
                  <Select.Option key={opt.id} value={opt.id}>
                    {opt.label}
                    {opt.recommended && ' (추천)'}
                  </Select.Option>
                ))}
              </Select>
            )
          }
        ]}
        dataSource={conflictList}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
      <Button
        type="primary"
        onClick={handleSave}
        loading={loading}
        style={{ marginTop: 16 }}
      >
        충돌 해결 및 계속
      </Button>
    </div>
  );
};
```

### 성공 기준 (Task 8-2)
- [ ] 충돌 감지: 5가지 유형 (label, URI, property, range, domain)
- [ ] 충돌 표시: 외부 vs 내부 구분하여 표시
- [ ] 해결 옵션: 각 충돌마다 2~3개 옵션 제시
- [ ] 대량 충돌: 페이지네이션 (10개/페이지)

---

## Task 8-3: Provenance & 신뢰도 관리

**기간**: 07-18 ~ 07-19 (1.5일)

### 목표

임포트된 엔티티와 매핑의 출처, 신뢰도, 승인 상태를 투명하게 공개

### 구현 항목

#### 1) Provenance 정보 패널
```typescript
// src/components/ProvenancePanel.tsx
interface ProvenanceInfo {
  entityUri: string;
  entityLabel: string;
  importedAt: string;
  importJobId: string;
  sourceUri: string;
  sourceLabel: string;
  sourceVersion?: string;
  mappingRule?: {
    relationshipType: string;
    confidence: number;
    createdBy: string;
    approvedBy?: string;
    approvalStatus: 'pending' | 'approved' | 'rejected';
  };
  changeHistory: Array<{
    timestamp: string;
    action: string;
    performedBy: string;
    details: string;
  }>;
}

export const ProvenancePanel: React.FC<{
  provenance: ProvenanceInfo;
}> = ({ provenance }) => {
  return (
    <div className="provenance-panel">
      <Card title="기본 정보">
        <p><strong>엔티티</strong>: {provenance.entityLabel}</p>
        <p><strong>URI</strong>: <code>{provenance.entityUri}</code></p>
        <p><strong>출처</strong>: {provenance.sourceLabel}</p>
        <p><strong>Import Job ID</strong>: {provenance.importJobId}</p>
        <p><strong>Import 시간</strong>: {new Date(provenance.importedAt).toLocaleString()}</p>
      </Card>

      {provenance.mappingRule && (
        <Card title="매핑 정보" style={{ marginTop: 16 }}>
          <p><strong>관계 유형</strong>: <Tag>{provenance.mappingRule.relationshipType}</Tag></p>
          <p>
            <strong>신뢰도</strong>: 
            <span style={{
              color: provenance.mappingRule.confidence > 0.8 ? 'green' : 'orange'
            }}>
              {(provenance.mappingRule.confidence * 100).toFixed(0)}%
            </span>
          </p>
          <p><strong>생성자</strong>: {provenance.mappingRule.createdBy}</p>
          <p>
            <strong>상태</strong>: 
            <Tag color={
              provenance.mappingRule.approvalStatus === 'approved' ? 'green' :
              provenance.mappingRule.approvalStatus === 'rejected' ? 'red' : 'blue'
            }>
              {provenance.mappingRule.approvalStatus}
            </Tag>
          </p>
        </Card>
      )}

      <Card title="변경 이력" style={{ marginTop: 16 }}>
        <Timeline
          items={provenance.changeHistory.map(event => ({
            label: new Date(event.timestamp).toLocaleString(),
            children: (
              <div>
                <p><strong>{event.action}</strong></p>
                <p>{event.details}</p>
                <p style={{ color: '#999', fontSize: '12px' }}>by {event.performedBy}</p>
              </div>
            )
          }))}
        />
      </Card>
    </div>
  );
};
```

#### 2) 신뢰도 기반 필터링
```typescript
export const ConfidenceFilter: React.FC<{
  minConfidence: number;
  onChange: (confidence: number) => void;
}> = ({ minConfidence, onChange }) => {
  return (
    <div>
      <p>신뢰도 필터</p>
      <Slider
        min={0}
        max={100}
        value={minConfidence * 100}
        onChange={(val) => onChange(val / 100)}
        marks={{ 0: '0%', 50: '50%', 80: '80%', 100: '100%' }}
      />
    </div>
  );
};
```

### 성공 기준 (Task 8-3)
- [ ] Provenance 패널: 기본 정보, 매핑, 변경 이력 3섹션
- [ ] 신뢰도 필터: 슬라이더로 신뢰도 임계값 설정
- [ ] 모든 매핑의 출처와 승인 상태 공개

---

## 🎯 전체 성공 기준 (Week 8)

### E2E 통합 목표
- [ ] 마법사: 6단계 완전한 흐름 (업로드 → 완료)
- [ ] E2E 테스트: 5+ 시나리오 커버

### 충돌 처리 목표
- [ ] 충돌 감지: 5가지 유형
- [ ] 해결 옵션: 각 충돌마다 2~3개

### Provenance 목표
- [ ] Provenance 정보: 기본, 매핑, 변경 이력
- [ ] 신뢰도 시각화 및 필터

---

## 📋 보고서 저장 지시

**저장 경로**: `task_logs/codex/YYYYMMDD_HHMM_PHASE4_WEEK8_Codex_Complete.md`

**예시**: `20260719_1830_PHASE4_WEEK8_Codex_Complete.md`

**보고서 항목**:
1. Task 8-1: E2E 파이프라인 완성도
2. Task 8-2: 충돌 처리 기능
3. Task 8-3: Provenance 및 신뢰도 관리
4. PoC 평가 및 개선 제안

**완료 후**: Claude가 3개 보고서를 취합하여 통합 보고서를 작성합니다.
(`task_logs/consolidated/YYYYMMDD_HHMM_PHASE4_WEEK8_Consolidated_Report.md`)
