# 05_30_ChkJdkEnv.py 핵심 내용
import jpype
jvm_path = r"D:\Java\jdk-17\bin\server\jvm.dll" # 설정한 경로 확인
if not jpype.isJVMStarted():
    jpype.startJVM(jvm_path)
print("🚀 JVM이 성공적으로 시작되었습니다!")