import pandas as pd
import streamlit as st

st.set_page_config(page_title="공장 반복 고장 분석", layout="wide")
st.title("공장 반복 고장 분석")

data = pd.DataFrame([
    {"설비": "검사 카메라", "고장횟수": 3, "상태": "정비 필요"},
    {"설비": "배터리 탭 용접기", "고장횟수": 2, "상태": "관찰"},
    {"설비": "압력 센서", "고장횟수": 1, "상태": "정상 확인"},
])

metric_cols = st.columns(3)
metric_cols[0].metric("반복 고장 설비", len(data[data["고장횟수"] >= 2]))
metric_cols[1].metric("총 고장 횟수", int(data["고장횟수"].sum()))
metric_cols[2].metric("정비 필요", int((data["상태"] == "정비 필요").sum()))

st.subheader("설비별 반복 고장 그래프")
chart_data = data.set_index("설비")["고장횟수"]
st.bar_chart(chart_data)

st.subheader("일자별 고장 추이")
trend = pd.DataFrame({
    "일자": ["D-6", "D-5", "D-4", "D-3", "D-2", "D-1", "오늘"],
    "검사 카메라": [0, 1, 0, 1, 0, 0, 1],
    "배터리 탭 용접기": [1, 0, 0, 0, 1, 0, 0],
})
st.line_chart(trend.set_index("일자"))

st.subheader("상세 목록")
st.dataframe(data, use_container_width=True)