import os
import sys
import gc
import asyncio
import tracemalloc
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import AsyncIterator, List, Dict, Any, Tuple, Optional
from rdflib import Graph, URIRef, Literal, Namespace

class StreamingRDFLoader:
    """스트리밍 방식의 대용량 RDF 파일 로더"""

    async def load_large_rdf_file(self, 
                                 file_path: str,
                                 batch_size: int = 1000) -> AsyncIterator[Graph]:
        """대용량 N-Triples 파일을 읽고 batch_size 단위로 rdflib.Graph를 생성하여 양보(yield)"""
        graph = Graph()
        triple_count = 0
        
        # 파일이 실제로 존재하지 않으면 즉시 빈 그래프 양보 후 종료
        if not os.path.exists(file_path):
            yield graph
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                clean_line = line.strip()
                if not clean_line or clean_line.startswith('#'):
                    continue
                
                # N-Triples 행은 온전한 문장 끝에 온점(.)이 있어야 함
                if clean_line.endswith('.'):
                    try:
                        triple = self._parse_ntriple(clean_line)
                        if triple:
                            graph.add(triple)
                            triple_count += 1
                    except Exception:
                        # 파싱 실패한 라인은 스킵
                        continue

                    # 지정한 배치 크기 도달 시 양보
                    if triple_count >= batch_size:
                        yield graph
                        graph = Graph()
                        triple_count = 0
                        # 이벤트 루프에 제어권을 양보하여 비동기 동시성 보장 및 CPU 블로킹 방지
                        await asyncio.sleep(0)
        
        # 남은 트리플 잔량 양보
        if len(graph) > 0:
            yield graph

    def _parse_ntriple(self, line: str) -> Optional[Tuple[URIRef, URIRef, Any]]:
        """N-Triple 단일 행 파싱 (<subject> <predicate> <object> .)"""
        # 온점(.) 및 양끝 공백 제거
        raw = line.strip()
        if raw.endswith('.'):
            raw = raw[:-1].strip()

        # 공백 기준으로 주어/술어/목적어 3분할
        # 객체 영역에 공백이 들어갈 수 있으므로 split(' ', 2) 사용
        parts = raw.split(' ', 2)
        if len(parts) < 3:
            return None

        s_str, p_str, o_str = parts[0].strip(), parts[1].strip(), parts[2].strip()

        # URIRef 혹은 Literal 파싱
        s = URIRef(s_str[1:-1]) if s_str.startswith('<') and s_str.endswith('>') else URIRef(s_str)
        p = URIRef(p_str[1:-1]) if p_str.startswith('<') and p_str.endswith('>') else URIRef(p_str)
        
        if o_str.startswith('<') and o_str.endswith('>'):
            o = URIRef(o_str[1:-1])
        elif o_str.startswith('"') and o_str.endswith('"'):
            o = Literal(o_str[1:-1])
        else:
            # 리터럴 데이터타입 매칭 처리
            if "^^" in o_str:
                val, dt = o_str.split("^^", 1)
                val = val.strip('"')
                dt_uri = dt.strip('<>')
                o = Literal(val, datatype=URIRef(dt_uri))
            else:
                o = Literal(o_str)

        return (s, p, o)


class ParallelGraphProcessor:
    """멀티프로세싱 기반 병렬 RDF 그래프 연산 프로세서"""

    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers

    def process_graphs_parallel(self, graphs: List[Graph]) -> List[Graph]:
        """전달된 그래프 리스트를 멀티프로세스로 분산하여 가공 및 인덱싱 처리"""
        # rdflib Graph 객체는 복잡하여 직접 직렬화(pickle) 시 일부 오버헤드가 발생하므로
        # 트리플 튜플 목록으로 변환하여 프로세스 풀로 전송하고, 반환값을 다시 Graph로 재복구하는 것이 훨씬 안전하고 효율적입니다.
        serialized_graphs = []
        for g in graphs:
            triples = [(str(s), str(p), str(o)) for s, p, o in g]
            serialized_graphs.append(triples)

        results = []
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            future_to_index = {
                executor.submit(self._process_single_graph_serialized, triples): i
                for i, triples in enumerate(serialized_graphs)
            }
            
            # 병렬 연산 태스크 완료 대기
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    processed_triples = future.result()
                    # 다시 Graph로 변환
                    res_graph = Graph()
                    for s, p, o in processed_triples:
                        s_ref = URIRef(s)
                        p_ref = URIRef(p)
                        o_ref = URIRef(o) if o.startswith("http://") or o.startswith("https://") else Literal(o)
                        res_graph.add((s_ref, p_ref, o_ref))
                    results.append(res_graph)
                except Exception as e:
                    logger.error("Error processing graph at index %d: %s", idx, e)
                    # 오류 발생 시 원본 그래프 그대로 복구
                    results.append(graphs[idx])

        return results

    @staticmethod
    def _process_single_graph_serialized(triples: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """단일 프로세스 내부에서 가공 및 인덱싱 연산 시뮬레이션 (Pickle 가능)"""
        # 무거운 CPU 연산 부하 시뮬레이션
        hash_val = 0
        for _ in range(50000):
            hash_val = (hash_val + 42) % 10007

        processed = []
        for s, p, o in triples:
            # 간단한 URI 노멀라이즈 등 가공
            processed.append((s, p, o))
        return processed


class MemoryEfficientRDFProcessor:
    """메모리 최소 점유형 RDF 제너레이터 및 증분 병합 처리기"""

    def _parse_ntriple(self, line: str) -> Tuple[URIRef, URIRef, Any]:
        loader = StreamingRDFLoader()
        return loader._parse_ntriple(line)

    def process_with_generator(self, file_path: str):
        """생성자(Generator) 패턴을 이용한 점진적 텍스트 트리플 스트리밍 가공"""
        def triple_generator():
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line and not clean_line.startswith('#') and clean_line.endswith('.'):
                        triple = self._parse_ntriple(clean_line)
                        if triple:
                            yield triple

        for s, p, o in triple_generator():
            # 대량 로드 시 메모리에 적재하지 않고 즉시 비즈니스 파이프라인으로 전송
            pass

    def merge_graphs_incrementally(self, graph_files: List[str]) -> Graph:
        """증분식(Incremental) 그래프 로드 및 누적 병합 (동시 메모리 로드 억제)"""
        merged = Graph()
        for file_path in graph_files:
            if not os.path.exists(file_path):
                continue
            
            # 임시 그래프 객체를 사용해 파일 파싱
            temp_graph = Graph()
            temp_graph.parse(file_path, format='ntriples')
            
            # 병합
            for s, p, o in temp_graph:
                merged.add((s, p, o))
            
            # gc 가동을 위해 임시 그래프 메모리 할당 즉시 해제
            del temp_graph
            gc.collect()

        return merged

    def get_memory_stats(self) -> Dict[str, float]:
        """tracemalloc 기반의 현재 메모리 및 peak 메모리 상태 획득"""
        current, peak = tracemalloc.get_traced_memory()
        return {
            'current_mb': current / (1024 * 1024),
            'peak_mb': peak / (1024 * 1024)
        }
