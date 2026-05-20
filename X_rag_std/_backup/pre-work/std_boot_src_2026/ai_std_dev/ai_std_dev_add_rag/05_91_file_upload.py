import os
import shutil

# [하드코딩] 05_9x 시리즈 전용 실습 경로 (rag_1 서비스와 격리)
PROJECT_RAW_DIR = r"F:\ai_std_dev\data\qabot\05_91\P05_91_BASIC\raw"

def run_upload(local_file_path):
    print(f"=== [05_91] 파일 업로드 단계 시작 ===")
    
    try:
        # 1. 실습 전용 폴더 생성
        if not os.path.exists(PROJECT_RAW_DIR):
            os.makedirs(PROJECT_RAW_DIR)
            print(f"> 신규 실습 폴더 생성: {PROJECT_RAW_DIR}")

        # 2. 파일 물리적 복사 실행 (shutil 사용)
        file_name = os.path.basename(local_file_path)
        target_path = os.path.join(PROJECT_RAW_DIR, file_name)
        shutil.copyfile(local_file_path, target_path)
        
        print("-" * 50)
        print(f"성공: [{file_name}] 업로드 완료")
        print(f"위치: {target_path}")
        print("-" * 50)
        return target_path

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return None

if __name__ == "__main__":
    # 테스트용 파일 (파일명이 일치해야 함)
    test_pdf = "./2025년 AI바우처 사업설명회 발표자료.pdf" 
    if os.path.exists(test_pdf):
        run_upload(test_pdf)
    else:
        print(f"파일을 찾을 수 없습니다: {test_pdf}")