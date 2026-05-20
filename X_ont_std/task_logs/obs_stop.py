import obsws_python as obs

try:
    client = obs.ReqClient(host="localhost", port=4455, password="")
    client.stop_record()
    print("OBS 녹화 중지 완료")
except Exception as e:
    print(f"OBS 녹화 중지 실패: {e}")
