import pandas as pd
import plotly.express as px
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="서울 100년 기온 변화 분석", page_icon="🌡️", layout="wide"
)

# 제목 및 설명
st.title("🌡️ 지난 100년간 서울의 연평균 기온 변화")
st.markdown(
    """
구글/공공데이터의 **서울 기온 데이터(seoul.csv)**를 분석하여 100년 동안 서울의 기온이 어떻게 변해왔는지 보여주는 앱입니다.
"""
)


# 데이터 로드 및 전처리 (캐싱 적용)
@st.cache_data
def load_data():
  url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

  # CSV 읽기 (한글 컬럼 대응)
  df = pd.read_csv(url, encoding="cp949")

  # 컬럼명 공백 제거
  df.columns = df.columns.str.strip()

  # '날짜' 컬럼을 datetime으로 변환
  df["날짜"] = pd.to_datetime(df["날짜"])

  # '연도' 추출
  df["연도"] = df["날짜"].dt.year

  # '평균기온(℃)' 컬럼 수치형 변환 (결측치 제외)
  df["평균기온(℃)"] = pd.to_numeric(df["평균기온(℃)"], errors="coerce")

  # 연도별 평균 기온 계산 (데이터가 너무 적은 연도 제외를 위해 count 체크 가능)
  yearly_df = df.groupby("연도")["평균기온(℃)"].mean().reset_index()

  # 최근 연도 중 데이터가 불완전한 해가 있을 수 있으므로 연도별 데이터 개수 300일 이상인 해만 포함
  valid_years = df.groupby("연도")["평균기온(℃)"].count()
  valid_years = valid_years[valid_years >= 300].index
  yearly_df = yearly_df[yearly_df["연도"].isin(valid_years)]

  return df, yearly_df


try:
  with st.spinner("데이터를 불러오는 중입니다..."):
    raw_df, yearly_df = load_data()

  # 추세선(3차 회귀)을 포함한 선 그래프 생성
  fig = px.line(
      yearly_df,
      x="연도",
      y="평균기온(℃)",
      title="서울 연평균 기온 추이 (100년)",
      markers=True,
      labels={"연도": "연도 (Year)", "평균기온(℃)": "연평균 기온 (℃)"},
  )

  # 추세선 추가 (OLS 회귀선)
  fig_trend = px.scatter(
      yearly_df, x="연도", y="평균기온(℃)", trendline="ols"
  )
  trend_trace = fig_trend.data[1]
  trend_trace.line.color = "red"
  trend_trace.line.dash = "dash"
  trend_trace.name = "온도 상승 추세선"
  fig.add_trace(trend_trace)

  # 그래프 스타일 변경
  fig.update_layout(
      hovermode="x unified",
      xaxis=dict(showgrid=True),
      yaxis=dict(showgrid=True),
  )

  # 주요 지표 표시 (Metrics)
  col1, col2, col3, col4 = st.columns(4)

  min_year = yearly_df["연도"].min()
  max_year = yearly_df["연도"].max()
  start_temp = yearly_df.iloc[0]["평균기온(℃)"]
  end_temp = yearly_df.iloc[-1]["평균기온(℃)"]
  diff_temp = end_temp - start_temp

  col1.metric("분석 기간", f"{min_year}년 ~ {max_year}년")
  col2.metric(f"{min_year}년 연평균 기온", f"{start_temp:.1f} ℃")
  col3.metric(f"{max_year}년 연평균 기온", f"{end_temp:.1f} ℃")
  col4.metric(
      "기온 변화 폭",
      f"{end_temp:.1f} ℃",
      delta=f"{diff_temp:+.1f} ℃",
      delta_color="normal",
  )

  st.divider()

  # 그래프 출력
  st.plotly_chart(fig, use_container_width=True)

  # 상위/하위 연도 정보
  st.subheader("📌 주요 기록")
  col_highest, col_lowest = st.columns(2)

  top_5 = yearly_df.sort_values(by="평균기온(℃)", ascending=False).head(5)
  bottom_5 = yearly_df.sort_values(by="평균기온(℃)", ascending=True).head(5)

  with col_highest:
    st.write("🔥 **가장 무더웠던 해 TOP 5**")
    st.dataframe(
        top_5.rename(
            columns={"연도": "연도", "평균기온(℃)": "연평균 기온(℃)"}
        ).style.format({"연평균 기온(℃)": "{:.2f} ℃"}),
        use_container_width=True,
        hide_index=True,
    )

  with col_lowest:
    st.write("❄️ **가장 추웠던 해 TOP 5**")
    st.dataframe(
        bottom_5.rename(
            columns={"연도": "연도", "평균기온(℃)": "연평균 기온(℃)"}
        ).style.format({"연평균 기온(℃)": "{:.2f} ℃"}),
        use_container_width=True,
        hide_index=True,
    )

  # 데이터 출처 및 설명
  with st.expander("📄 데이터 원본 보기"):
    st.dataframe(raw_df.head(100))

except Exception as e:
  st.error(f"데이터를 불러오거나 처리하는 중 오류가 발생했습니다: {e}")
