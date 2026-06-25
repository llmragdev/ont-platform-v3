# 03_SKILL_IMPLEMENTATION_SPEC.md 기술 검토 의견서

**작성일:** 2026-06-14  
**작성자:** Antigravity  
**대상 문서:** [03_SKILL_IMPLEMENTATION_SPEC.md](file:///E:/ontology_edu/X_ont_std/design/%EC%8A%A4%ED%82%AC/03_SKILL_IMPLEMENTATION_SPEC.md)

---

## 📋 요약

제시된 구현 명세서는 이전 검토 의견서(변수 바인딩, 인증 정보 분리, MCP 명세화, 샌드박스 가드레일)를 매우 구체적인 데이터 모델과 의사코드로 보완한 훌륭한 명세서입니다. 

그러나 실제 구현에 들어갔을 때 **서버가 오동작하거나 런타임 에러(Crash)를 유발할 수 있는 치명적인 기술적 문제 3가지**를 발견했습니다. 이들에 대한 상세 원인과 해결 코드를 제안합니다.

---

## 🚨 치명적인 오류 및 개선 의견 (Critical Issues)

### 1. Windows 환경에서의 `signal.alarm` 사용 불가 문제 (플랫폼 호환성 버그)
* **원인:** 명세서 **Section 7.2**의 `execute_custom_code_with_timeout` 함수는 `signal.SIGALRM` 및 `signal.alarm`을 사용해 실행 시간을 제한합니다.
  ```python
  signal.signal(signal.SIGALRM, timeout_handler)
  signal.alarm(timeout_sec)
  ```
  그러나 **Windows 운영체제는 `signal.alarm` 및 `SIGALRM` 신호를 지원하지 않습니다.** (Windows 환경에서 실행 시 `AttributeError`가 발생하며 서버 프로세스가 크래시됩니다. 현재 사용자 개발환경은 **Windows**입니다.)
* **해결책:** 크로스 플랫폼(Windows/Linux)을 모두 지원하는 **`multiprocessing` 프로세스 풀** 또는 **`concurrent.futures` 쓰레드/프로세스 풀**을 사용해야 합니다.
  * *권한/샌드박스 격리* 관점에서도 별도의 Python 서브프로세스를 기동하여 메인 백엔드 메모리와 완전히 격리한 상태에서 코드를 실행하고 중단(terminate)하는 것이 가장 안전합니다.

#### 💡 개선된 파이썬 프로세스 타임아웃 실행 코드 (Cross-Platform):
```python
import multiprocessing
import queue
from typing import Dict, Any

def _raw_run_code(code: str, input_data: Dict, result_queue: multiprocessing.Queue):
    """서브프로세스 내부에서 독립 실행되는 헬퍼"""
    try:
        exec_globals = {'input': input_data, 'output': None}
        # AST 검증을 통과한 코드만 들어온다고 가정
        exec(code, exec_globals)
        result_queue.put({"success": True, "output": exec_globals.get('output')})
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})

def execute_custom_code_with_timeout(code: str, input_data: Dict, timeout_sec: int = 3) -> Any:
    """Windows와 Linux 모두 작동하며 프로세스 격리를 제공하는 안전한 타임아웃 실행 함수"""
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_raw_run_code, 
        args=(code, input_data, result_queue)
    )
    process.start()
    
    # 지정한 초만큼 완료 대기
    process.join(timeout=timeout_sec)
    
    if process.is_alive():
        process.terminate()  # 타임아웃 초과 시 서브프로세스 즉각 강제 강제 중단
        process.join()       # 좀비 프로세스 방지
        raise TimeoutError(f"Custom code execution exceeded limit of {timeout_sec}s")
        
    try:
        res = result_queue.get_nowait()
        if not res["success"]:
            raise RuntimeError(res["error"])
        return res["output"]
    except queue.Empty:
        raise RuntimeError("No result returned from code process")
```

---

### 2. MCP JSON-RPC 초기화 프로토콜(Initialize Handshake) 누락
* **원인:** 명세서 **Section 4.3**의 `_execute_stdio` 함수를 보면, 프로세스를 실행하자마자 다이렉트로 `call_tool` 요청 프레임을 전송합니다.
  ```python
  request = {
      "jsonrpc": "2.0",
      "method": "call_tool",
      "params": { ... }
  }
  ```
  표준 MCP 규격에 따르면, 클라이언트는 세션 시작 직후 반드시 **`initialize` 핸드셰이크** 요청을 보내 서버의 기능을 조율(Negotiation)하고 응답을 받은 뒤 `initialized` 알림을 전송해야 합니다. 이 과정 없이 `call_tool`을 호출하면 표준 MCP 서버들은 요청을 무시하거나 프로토콜 위반 에러를 반환합니다.
* **해결책:** Stdio 연결 후 최초 1회 초기화 시퀀스를 수행하도록 코드를 보완해야 합니다.
  * **초기화 프레임 예시:**
    1. 요청: `method: "initialize"`, `params: { "protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": { "name": "ontology-console", "version": "1.0" } }`
    2. 응답 수신 대기
    3. 알림 전송: `method: "notifications/initialized"` (JSON-RPC notification - `id` 없음)
    4. 실제 작업 수행: `method: "tools/call"` (도구 호출 시 표준 주소는 `tools/call` 또는 `call_tool` 이며 최신 규격은 `tools/call` 입니다.)

---

### 3. 변수 바인딩 시 데이터 타입 캐스팅(Casting) 오류
* **원인:** 명세서 **Section 2.3**의 `prepareSkillInput` 프론트엔드 함수 및 백엔드 파서에서 템플릿 스트링(`"{{...}}"`)을 평가할 때 일괄적으로 문자열로 보간(`evaluateExpression`)한 후 할당합니다.
  ```typescript
  if (typeof value === 'string' && value.includes('{{')) {
    prepared[key] = evaluateExpression(value, executionContext); // -> 무조건 string 반환
  }
  ```
  그러나 스킬의 입력 중에는 `limit` (정수), `params` (객체), `cc` (문자열 리스트) 등 **비-문자열(Non-string) 구조체**가 빈번하게 사용됩니다.
  만약 `{{nodes.n-asset-map.output.equipmentIdList}}`가 정수 배열 `[102, 103]` 이라면, 결과값이 문자열 `"[102, 103]"`으로 강제 캐스팅되어 유효성 검사(`inputSchema`)를 통과하지 못하게 됩니다.
* **해결책:** 만약 템플릿 필드의 값이 텍스트 보간 없이 **오직 단 하나의 표현식으로만 이루어져 있다면(예: `value === '{{nodes.nodeId.output.field}}'`)**, 문자열 치환 대신 원본 데이터의 타입을 그대로 상속(preserve type)하여 매핑해야 합니다.

#### 💡 개선된 표현식 파서 규칙 (Python 예시):
```python
import re
from typing import Any, Dict

# 단일 표현식 판별용 정규식 (앞뒤 다른 텍스트가 없는 경우)
SINGLE_EXPR_PATTERN = r'^\{\{([^{}]+)\}\}$'

def resolve_input_value(value: Any, execution_context: Dict) -> Any:
    if not isinstance(value, str):
        return value
        
    # Case A: 오직 표현식 하나만 존재하는 경우 (원본 데이터 타입 유지)
    single_match = re.match(SINGLE_EXPR_PATTERN, value.strip())
    if single_match:
        expr_path = single_match.group(1).strip()
        return evaluate_expression(expr_path, execution_context)
        
    # Case B: 텍스트 템플릿 내부에 혼합되어 있는 경우 (문자열 보간)
    def replacer(match):
        expr_path = match.group(1).strip()
        return str(evaluate_expression(expr_path, execution_context))
        
    return re.sub(r'\{\{([^{}]+)\}\}', replacer, value)
```

---

## 🛠️ 추가적인 권고사항 (Recommendations)

1. **Stdio 프로세스 재사용 레이어 (성능 최적화)**
   - MVP 수준에서는 매 도구 호출마다 `subprocess.Popen`으로 `npx`를 새로 실행하는 것이 구현하기 간편하지만, 매 호출마다 2~3초의 기동 딜레이가 추가됩니다.
   - Phase 2 구현 시에는 서버 프로세스를 백엔드 메모리에 풀(Process Pool)이나 서비스 인스턴스 형태로 유지하며 파이프(pipe)를 계속 살려두는 **프로세스 관리 라이프사이클**을 구축해야 서비스 지연을 막을 수 있습니다.
2. **도구 호출 표준 규격 맞춤**
   - 최신 MCP 스펙 기준 도구 호출 명령어는 `call_tool`이 아닌 `tools/call` 입니다. 백엔드 전송 시 이를 반영하여 표준을 준수하는 것이 호환성 확보에 유리합니다.
