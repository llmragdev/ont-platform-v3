# Phase 4 Week 6: Performance Optimization
## Codex (Frontend) 수행 지시서

**기간**: 2026-07-01 ~ 2026-07-05 (5일)  
**할당**: 80% (주당 24-30시간)  
**목표**: 프론트엔드 성능 최적화, 번들 크기 감소, 핵심 Web Vitals 개선

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
npm run dev  # 포트 3002

# 성능 분석 및 테스트
npm run build
npm run analyze
npm test -- --coverage
```

**npm 환경 위치**: `C:\Users\nkchoi2\anaconda3\envs\claud_fe`

---

## Task 6-1: 번들 크기 최적화

**기간**: 07-01 ~ 07-02 (1.5일)

### 목표
프로덕션 번들 크기 30% 감소 및 로드 시간 50% 단축

### 작업 항목

#### 1) 번들 분석 및 최적화
```bash
# 현재 번들 분석
npm run build
npm run analyze

# 목표:
# Main bundle: 200KB → 140KB (30%)
# SPARQL Workbench chunk: 150KB → 100KB
# QueryBuilder chunk: 120KB → 80KB
```

#### 2) 코드 분할 전략
```typescript
// webpack.config.ts 또는 next.config.ts
export default {
  optimization: {
    splitChunks: {
      cacheGroups: {
        // 벤더 라이브러리 분리
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          priority: 10,
          reuseExistingChunk: true,
        },
        // React 생태계 분리
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react-vendors',
          priority: 20,
        },
        // SPARQL 관련 라이브러리
        sparql: {
          test: /[\\/]node_modules[\\/](sparqljs|rdf-js)[\\/]/,
          name: 'sparql-lib',
          priority: 15,
        },
        // 공통 코드
        common: {
          minChunks: 2,
          priority: 5,
          reuseExistingChunk: true,
          name: 'common',
        },
      },
    },
  },
};

// 라우트 기반 코드 분할
const SPARQLWorkbench = lazy(() => import('./components/SPARQLWorkbench'));
const QueryBuilder = lazy(() => import('./components/QueryBuilder'));
const WriteBackMonitor = lazy(() => import('./components/WriteBackMonitor'));

export const AppRoutes = () => (
  <Routes>
    <Route path="/sparql" element={<SPARQLWorkbench />} />
    <Route path="/query-builder" element={<QueryBuilder />} />
    <Route path="/monitor" element={<WriteBackMonitor />} />
  </Routes>
);
```

#### 3) 라이브러리 최적화
```typescript
// 번들 크기 큰 라이브러리 최적화
import { debounce } from 'lodash-es'; // ❌ 전체 로드
import debounce from 'lodash-es/debounce'; // ✅ 개별 함수만 로드

// 불필요한 polyfill 제거
// 타겟 브라우저 명확히 (IE11 지원 불필요)
{
  "browserslist": [
    "last 2 Chrome versions",
    "last 2 Firefox versions",
    "last 2 Safari versions",
    "Edge >= 90"
  ]
}

// 큰 라이브러리 대체
// moment → date-fns (더 작음)
import { format } from 'date-fns';

// axios → fetch API (필요시 작은 wrapper)
const fetchJSON = async (url: string) => {
  const response = await fetch(url);
  return response.json();
};
```

#### 4) 이미지 및 에셋 최적화
```typescript
// 이미지 최적화
import Image from 'next/image';

<Image
  src="/sparql-icon.png"
  alt="SPARQL Icon"
  width={24}
  height={24}
  priority={false} // 필요시만 우선로드
/>

// SVG 인라인 (작은 것)
import SPARQLIcon from '@/assets/sparql-icon.svg';

<SVGIcon component={SPARQLIcon} />

// 폰트 최적화
import { Poppins, JetBrains_Mono } from 'next/font/google';

const poppins = Poppins({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  display: 'swap', // FOUT 대신 FOIT
});
```

### 번들 목표
- [ ] Main bundle: < 140KB (gzip)
- [ ] 라우트별 청크: < 100KB (각 주요 기능)
- [ ] 초기 로드 시간: < 2초
- [ ] 라우트 전환: < 500ms

---

## Task 6-2: Core Web Vitals 개선

**기간**: 07-02 ~ 07-04 (2일)

### 목표
LCP < 2.5s, FID < 100ms, CLS < 0.1

### 1) 최대 콘텐츠 유화 (Largest Contentful Paint)
```typescript
// LCP 최적화: < 2.5초
// 1. 중요 리소스 사전 로드
<link rel="preload" as="script" href="/main.js" />
<link rel="prefetch" as="style" href="/sparql.css" />

// 2. 이미지 최적화
<Image
  src="/sparql-workbench.png"
  alt="SPARQL Workbench"
  sizes="(max-width: 768px) 100vw, 80vw"
  priority={true} // 위의 이미지는 우선로드
/>

// 3. 폰트 로드 최적화
const fontDisplay = 'swap'; // FOUT (Flash of Unstyled Text)

// 4. 백그라운드 작업 최적화
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => {
    // 낮은 우선순위 작업
    loadAnalytics();
    initializeTooltips();
  });
}
```

### 2) 첫 입력 지연 (First Input Delay)
```typescript
// FID 최적화: < 100ms
// 1. 이벤트 리스너 효율화
const handleQueryChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
  // 무거운 작업은 debounce
  debouncedValidateQuery(e.target.value);
}, []);

// 2. Long Task 분할
const validateQueryAsync = async (query: string) => {
  // 크기가 큰 작업을 작은 청크로 분할
  const chunks = query.split('\n');
  
  for (const chunk of chunks) {
    // 메인 스레드 블로킹 방지
    await new Promise(resolve => setTimeout(resolve, 0));
    validateChunk(chunk);
  }
};

// 3. Web Worker 활용 (무거운 계산)
const queryWorker = new Worker('/workers/query-validator.js');

queryWorker.onmessage = (e) => {
  const { isValid, errors } = e.data;
  setValidationErrors(errors);
};

queryWorker.postMessage({ query });
```

### 3) 누적 레이아웃 변화 (Cumulative Layout Shift)
```typescript
// CLS 최적화: < 0.1
// 1. 이미지 크기 사전 지정
<Image
  src="/result-table.png"
  width={800}
  height={600}
  alt="Results"
/>

// 2. 글꼴 크기 일관성
// CSS custom properties 사용
:root {
  --font-size-base: 16px;
  --line-height: 1.5;
}

// 3. 레이아웃 안정성
// ❌ 틀린 예
{isLoading && <Spinner />}  // 레이아웃 변화

// ✅ 올바른 예
<div style={{ minHeight: '100px' }}>
  {isLoading ? <Spinner /> : <Results />}
</div>

// 4. 페이지네이션 안정성
const [page, setPage] = useState(1);

return (
  <div style={{ minHeight: '1000px' }}> {/* 고정 높이 */}
    <ResultsTable data={currentPageData} />
    <Pagination page={page} onChange={setPage} />
  </div>
);
```

### Web Vitals 목표
- [ ] LCP: < 2.5초
- [ ] FID: < 100ms
- [ ] CLS: < 0.1
- [ ] TTFб: < 1.5초

---

## Task 6-3: 렌더링 성능 최적화

**기간**: 07-04 ~ 07-05 (1.5일)

### 1) 컴포넌트 최적화
```typescript
// 메모이제이션
const SPARQLWorkbench = memo(({ initialQuery }: Props) => {
  // 구현
}, (prevProps, nextProps) => {
  // 커스텀 비교: initialQuery 변경 시만 리렌더링
  return prevProps.initialQuery === nextProps.initialQuery;
});

// useMemo & useCallback
const SearchResults = ({ results }: Props) => {
  // 결과 정렬은 results 변경시만 재계산
  const sortedResults = useMemo(
    () => results.sort((a, b) => a.score - b.score),
    [results]
  );

  // 콜백은 메모이제이션
  const handleSelectResult = useCallback((result) => {
    console.log(result);
  }, []);

  return <ResultsList data={sortedResults} onSelect={handleSelectResult} />;
};
```

### 2) 가상화 (Virtualization)
```typescript
// 대량 데이터 렌더링 최적화 (1000+ 행)
import { FixedSizeList } from 'react-window';

const LargeResultsTable = ({ results }: Props) => {
  const Row = ({ index, style }: any) => (
    <div style={style} className="result-row">
      <span>{results[index].subject}</span>
      <span>{results[index].predicate}</span>
      <span>{results[index].object}</span>
    </div>
  );

  return (
    <FixedSizeList
      height={600}
      itemCount={results.length}
      itemSize={35}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
};
```

### 3) 점진적 렌더링
```typescript
// Suspense를 활용한 점진적 로딩
<Suspense fallback={<SPARQLSkeleton />}>
  <SPARQLWorkbench />
</Suspense>

// Streaming SSR (Next.js 13+)
// app/sparql/page.tsx
export default async function SPARQLPage() {
  return (
    <div>
      <Suspense fallback={<ResultsSkeleton />}>
        <ResultsStream query={searchParams.q} />
      </Suspense>
    </div>
  );
}
```

### 렌더링 목표
- [ ] 초기 렌더링: < 100ms
- [ ] 상호작용성: < 50ms (SPARQL 쿼리 입력)
- [ ] 대량 데이터 렌더링: 1000+ 행 < 60fps

---

## 📊 성능 모니터링

```typescript
// 성능 메트릭 수집
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);

// 커스텀 메트릭
const reportMetric = (name: string, value: number) => {
  // Sentry, DataDog 등으로 전송
  console.log(`${name}: ${value}ms`);
};

// 라우트 전환 성능
router.events.on('routeChangeStart', () => {
  performanceStartMark = performance.now();
});

router.events.on('routeChangeComplete', () => {
  const duration = performance.now() - performanceStartMark;
  reportMetric('route-transition', duration);
});
```

---

## 🎯 성공 기준

- [x] 번들 크기: 30% 감소
- [x] LCP: < 2.5초
- [x] FID: < 100ms
- [x] CLS: < 0.1
- [x] 초기 로드: < 2초
- [x] 라우트 전환: < 500ms

---

**⚠️ 반드시 따르기**:

1. **저장 위치** (필수)
   - ✅ 정해진 위치: `task_logs/codex/YYYYMMDD_PHASE4_WEEK6_Codex_Complete.md`
   - 예: `20260705_1830_PHASE4_WEEK6_Codex_Complete.md`
   - ❌ 금지: `ont_platform/` 폴더에 저장하지 말 것

---

**상태**: Task 6-1~6-3 준비 완료  
**예상 완료**: 2026-07-05 (토요일)  
**다음 주차**: Week 7 Advanced UI & Visualization

---

## 📋 보고서 저장 지시

**저장 경로**: `task_logs/codex/YYYYMMDD_HHMM_PHASE4_WEEK6_Codex_Complete.md`

**예시**: `20260705_1830_PHASE4_WEEK6_Codex_Complete.md`

**완료 후**: Claude가 3개 보고서를 취합하여 통합 보고서를 작성합니다.
(`task_logs/consolidated/YYYYMMDD_HHMM_PHASE4_WEEK6_Consolidated_Report.md`)
