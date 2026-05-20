import os
import requests
import argparse
from sit_1_0_scenario_data import COMMON_UPLOAD_TASKS

BASE_URL = "http://127.0.0.1:8103"

def run_dynamic_upload(teams, company_id, proj_prefix):
    print(f"{'='*70}")
    print(f" [START] 1단계: RAG 공통 문서 적재 봇 (대상: {', '.join(teams)}) ")
    print(f"{'='*70}\n")

    for team_suffix in teams:
        p_id = f"{proj_prefix}{team_suffix}"
        print(f"▶▶ 적재 대상: [ {team_suffix}조 ] (Company: {company_id}, Project: {p_id})")
        
        for task in COMMON_UPLOAD_TASKS:
            if "file_name" in task:
                target_files = [os.path.join(task['local_dir'], task['file_name'])]
            else:
                target_files = [os.path.join(task['local_dir'], f) for f in os.listdir(task['local_dir']) if f.lower().endswith('.pdf')]

            for f_path in target_files:
                if not os.path.exists(f_path):
                    print(f"  [오류] 파일 없음: {f_path}")
                    continue

                with open(f_path, "rb") as f:
                    res_up = requests.post(f"{BASE_URL}/upload", data={
                        "company_id": company_id, "project_id": p_id,
                        "mid_cat": task['mid'], "sub_cat": task['sub']
                    }, files={"file": f})
                
                if res_up.status_code == 200:
                    print(f"  - [업로드 완료] {os.path.basename(f_path)}")
                else:
                    print(f"  - [업로드 실패] HTTP {res_up.status_code}: {os.path.basename(f_path)}")
        print("-" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="동적 파라미터 기반 업로드 봇")
    parser.add_argument("-t", "--teams", nargs="+", required=True, help="조 접미사 (예: 1 2 apple)")
    parser.add_argument("-c", "--company", type=str, default="05_90")
    parser.add_argument("--prefix", type=str, default="project_")
    args = parser.parse_args()
    
    run_dynamic_upload(args.teams, args.company, args.prefix)