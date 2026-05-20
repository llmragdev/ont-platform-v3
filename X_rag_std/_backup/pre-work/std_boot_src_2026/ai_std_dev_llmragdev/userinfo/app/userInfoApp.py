import pandas as pd
import streamlit as st

from userinfo.biz.userInfoBiz import UserInfoBizService


@st.cache_resource
def get_biz_service() -> UserInfoBizService:
    return UserInfoBizService()


def _to_dataframe(users):
    return pd.DataFrame(
        [
            {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at,
            }
            for user in users
        ]
    )


def render_user_info_page():
    st.title("사용자 정보 조회")

    with st.sidebar:
        st.subheader("조회 조건")
        keyword = st.text_input("이름 또는 이메일", placeholder="예: Kim 또는 user@example.com")
        limit = st.slider("최대 조회 건수", min_value=10, max_value=500, value=100, step=10)
        search_clicked = st.button("조회", type="primary", use_container_width=True)

    if "last_keyword" not in st.session_state:
        st.session_state.last_keyword = ""
    if "last_limit" not in st.session_state:
        st.session_state.last_limit = 100
    if search_clicked:
        st.session_state.last_keyword = keyword
        st.session_state.last_limit = limit

    active_keyword = st.session_state.last_keyword
    active_limit = st.session_state.last_limit

    try:
        service = get_biz_service()
        users = service.search_users(active_keyword, active_limit)
        summary = service.get_summary(active_keyword)
    except Exception as exc:
        st.error(f"사용자 정보를 조회하지 못했습니다: {exc}")
        st.stop()

    col_count, col_keyword, col_limit = st.columns(3)
    col_count.metric("조회 대상 건수", summary.total_count)
    col_keyword.metric("검색어", summary.keyword or "전체")
    col_limit.metric("표시 제한", active_limit)

    df = _to_dataframe(users)
    if df.empty:
        st.info("조회된 사용자가 없습니다.")
        return

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "user_id": st.column_config.NumberColumn("사용자 ID"),
            "name": st.column_config.TextColumn("이름"),
            "email": st.column_config.TextColumn("이메일"),
            "created_at": st.column_config.DatetimeColumn("생성일시", format="YYYY-MM-DD HH:mm:ss"),
        },
    )

    st.download_button(
        "CSV 다운로드",
        data=df.to_csv(index=False, encoding="utf-8-sig"),
        file_name="user_info_lookup.csv",
        mime="text/csv",
    )
