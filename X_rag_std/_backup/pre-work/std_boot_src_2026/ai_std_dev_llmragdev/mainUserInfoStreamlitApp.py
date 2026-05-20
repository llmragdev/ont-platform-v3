import streamlit as st

from userinfo.app.userInfoApp import render_user_info_page


def main():
    st.set_page_config(
        page_title="User Info Lookup",
        page_icon="",
        layout="wide",
    )
    render_user_info_page()


if __name__ == "__main__":
    main()
