import os
import requests
import argparse
import pandas as pd
from datetime import datetime
from sit_1_0_scenario_data import COMMON_VECTORIZE_TASKS
from config_2_advanced import BASE_DATA_DIR # 최상위 경로 임포트

BASE_URL = "http://127.0.0.1:8102"
SAVE_ROOT = os.path.join(BASE_DATA_DIR, "eval_results")

def run_dynamic_vectorize(teams, company_id, proj_prefix):
    print(f"{'='*70}")
    print(f" [START] 2단계: 벡터 DB 동기화 봇 (대상: {', '.join(teams)}) ")
    print(f"{'='*70}\n")

    os.makedirs(SAVE_ROOT, exist_ok=True)
    all_eval_data = []

    for team_suffix in teams:
        p_id = f"{proj_prefix}{team_suffix}"
        print(f"▶▶ 벡터화 대상: [ {team_suffix}조 ] (Project: {p_id})")
        
        for task in COMMON_VECTORIZE_TASKS:
            rel_path = f"{task['mid']}/{task['sub']}"
            status_msg = "Fail"
            res_detail = ""
            
            res_vec = requests.post(f"{BASE_URL}/vectorize", data={
                "company_id": company_id, "project_id": p_id,
                "target_v_id": task['target_v_id'], 
                "file_relative_path": rel_path
            })
            
            if res_vec.status_code == 200:
                res_detail = res_vec.json().get('status', 'OK')
                status_msg = "Success"
                print(f"  - V{task['target_v_id']} 동기화 성공 ({rel_path})")
            else:
                res_detail = f"HTTP Error {res_vec.status_code}"
                print(f"  - V{task['target_v_id']} 동기화 실패 ({res_vec.status_code})")

            all_eval_data.append({
                "Team_Suffix": team_suffix,
                "Project_ID": p_id,
                "Target_V_ID": task['target_v_id'],
                "Category_Path": rel_path,
                "Status": status_msg,
                "Detail": res_detail,
                "Execute_Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        print("-" * 70)

    # 전체 벡터화 결과 리포트 저장
    if all_eval_data:
        df = pd.DataFrame(all_eval_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(SAVE_ROOT, f"Vectorize_Report_{'_'.join(teams[:3])}_{timestamp}.csv")
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"\n[SAVE] 동기화 결과 리포트 저장 완료: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="동적 파라미터 기반 벡터화 봇")
    parser.add_argument("-t", "--teams", nargs="+", required=True, help="조 접미사 (예: 1 2 apple)")
    parser.add_argument("-c", "--company", type=str, default="05_90")
    parser.add_argument("--prefix", type=str, default="project_")
    args = parser.parse_args()
    
    run_dynamic_vectorize(args.teams, args.company, args.prefix)