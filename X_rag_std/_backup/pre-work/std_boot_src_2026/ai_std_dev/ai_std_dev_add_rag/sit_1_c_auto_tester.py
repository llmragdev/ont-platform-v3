import os
import time
import argparse
import requests
import pandas as pd
from datetime import datetime

# 공통 질문만 가져옵니다.
from sit_1_0_scenario_data import COMMON_QUESTIONS 
from config_2_advanced import BASE_DATA_DIR # 최상위 경로 임포트

BASE_URL = "http://127.0.0.1:8103"
SAVE_ROOT = os.path.join(BASE_DATA_DIR, "eval_results")

def run_evaluator(teams, company_id, proj_prefix):
    print(f"{'='*70}")
    print(f" [START] RAG 시스템 중간 평가 봇 (대상: {', '.join(teams)}) ")
    print(f"{'='*70}\n")

    os.makedirs(SAVE_ROOT, exist_ok=True)
    all_eval_data = []

    # 파라미터로 받은 조(팀) 목록을 순회
    for team_suffix in teams:
        # [핵심 로직] 파라미터를 조합하여 동적으로 ID 생성
        p_id = f"{proj_prefix}{team_suffix}"  # 예: project_1, project_apple
        u_id = f"eval_master_{team_suffix}"
        
        current_session_id = None
        print(f"▶ 검증 대상: [ {team_suffix}조 ] (Company: {company_id}, Project: {p_id})")

        # 공통 질문 순차 질의
        for i, item in enumerate(COMMON_QUESTIONS, 1):
            params = {
                "company_id": company_id, 
                "project_id": p_id, 
                "target_group": item.get("v_id"), 
                "user_id": u_id,
                "question": item["q"]
            }
            if current_session_id:
                params["session_id"] = current_session_id

            try:
                response = requests.get(f"{BASE_URL}/ask", params=params, timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    current_session_id = data.get("session_id")
                    
                    eval_entry = {
                        "Eval_Round": "Interim_Eval",
                        "Team_Suffix": team_suffix,
                        "Project_ID": p_id,
                        "Session_ID": current_session_id,
                        "No": i,
                        "Question": item["q"],
                        "AI_Answer": data.get('answer', ''),
                        "Latency(s)": data.get('latency'),
                    }
                    
                    evidences = data.get('evidences', [])
                    if evidences:
                        # 첫 번째 근거 문서의 정보를 리포트 컬럼으로 할당
                        eval_entry["target_v_id"] = evidences[0].get('target_v_id') # V5001 등
                        eval_entry["category"] = evidences[0].get('category')   # 1001/2002 등

                    for idx, ev in enumerate(evidences, 1):
                        eval_entry[f"Ev_{idx}_Score"] = ev.get('score')
                        eval_entry[f"Ev_{idx}_Page"] = ev.get('page_no')
                        eval_entry[f"Ev_{idx}_File"] = ev.get('file')

                    all_eval_data.append(eval_entry)
                    print(f"  [성공] Q{i}: {item['q'][:25]}... (속도: {data.get('latency')}초)")
                else:
                    print(f"  [실패] Q{i}: API 에러 ({response.status_code})")
            except Exception as e:
                print(f"  [오류] 통신 실패: {str(e)}")
            
            time.sleep(1) # 과부하 방지 (1초 대기)

        # 다음 조로 넘어가기 전 쿨다운
        print(f"  * {team_suffix}조 평가 완료. 서버 쿨다운(3초) 대기 중...\n")
        time.sleep(3)
        print("-" * 70)

    # 전체 평가 결과 CSV 저장
    if all_eval_data:
        df = pd.DataFrame(all_eval_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Eval_Report_Teams_{'_'.join(teams[:3])}_{timestamp}.csv"
        file_path = os.path.join(SAVE_ROOT, file_name)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"[SAVE] 종합 채점표 저장 완료: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG 조별 자동 평가 봇 (동적 파라미터 적용)")
    
    # -t 1 2 3 apple 처럼 여러 개의 값을 리스트로 받습니다 (nargs="+")
    parser.add_argument("-t", "--teams", nargs="+", required=True, 
                        help="평가할 조의 접미사 (예: 1 2 3 apple)")
    
    # -c 파라미터를 주지 않으면 기본값 "05_90"을 사용합니다.
    parser.add_argument("-c", "--company", type=str, default="05_90", 
                        help="회사 ID (입력 생략 시 기본값 05_90 사용)")
    
    # 프로젝트 접두사도 혹시 몰라 유연하게 파라미터로 빼두었습니다.
    parser.add_argument("--prefix", type=str, default="project_", 
                        help="프로젝트 ID 접두사 (기본값: project_)")
    
    args = parser.parse_args()
    
    run_evaluator(args.teams, args.company, args.prefix)