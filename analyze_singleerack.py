import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import  matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from streamlit_echarts import st_echarts

server = r'10.89.29.56,51633\SQLEXPRESS'
database = 'INX_CERACK02'
username = 'sa'
password = '..cmo123'

#--set dashboard title and description---
st.set_page_config(page_title="ERACK DISABLE Events Analysis", page_icon="📊",layout="wide")

#-- confiurate connection to database parameters to cache---
@st.cache_resource
def get_db_engine():
    return create_engine(f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server')

# table_name = 'ERACK_EVENT_HISTORY'
engine = get_db_engine()


#-- function to fetch statistics from database based on query---
def run_tab1_query(engine):
    subheader = "DISABLE Events Count for Each ERACKID in the Last 4 Months"    
    try: 
        query_count = """select distinct b.ErackID, count(a.EventType) as disable_count from ERACK_EVENT_HISTORY a 
right join ERACK_INFO b 
on a.ErackID = b.ErackID
AND A.EventType = 'DISABLE'
AND CreateTime >= DATEADD(month,-4,GETDATE()) 
group by b.ErackID
"""
        df = pd.read_sql(query_count, engine)
       # 先用 st.subheader 寫標題
        st.subheader('DISABLE Events for Each ERACKID in the Last 4 Months') 
       # 長條圖呈現，但長條能夠被點擊選取，並且把選取的 ERACKID 傳到下一個分析的函式裡
        options = {
            "xAxis": {"type": "category", "data": df["ErackID"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": df["disable_count"].tolist(), "type": "bar"}],
        }
       #捕捉點擊事件
       # 在 run_tab1_query 函數內
        clicked = st_echarts(
                options=options, 
    events={"click": "function(params) { return params.name; }"}, 
    height="400px",
    key="erack_chart" # 加入 key 確保狀態穩定
        )
        # st.dataframe(df, use_container_width=True)
        return clicked
    except Exception as e:
        st.error(f"An error occurred while fetching data in tab1: {e}")
        return None
       # 移除 st.bar_chart 裡的 title 參數
        # st.bar_chart(data=df, x='ErackID', y='disable_count')
        # st.dataframe(df, use_container_width=True)
        # return df
   

def run_tab2_query(engine , selected_id):
    st.subheader(f"Analysis for {selected_id}")
    try: 
        # selected_id = st.selectbox("Select ERACKID to analyze DISABLE events trend:", id_list)
        if selected_id:
        #-- fetch disable and enable events for the selected ERACKID in the last 4 months ---
            query_detail = f"""SELECT EventType, CreateTime 
        FROM ERACK_EVENT_HISTORY 
        WHERE ErackID = '{selected_id}' 
        AND EventType IN ('DISABLE', 'ENABLE')
        AND CreateTime >= DATEADD(month, -4, GETDATE())
        ORDER BY CreateTime ASC """
            df_detail = pd.read_sql(query_detail, engine)
            if not df_detail.empty:
                #-- separate disable and enable events ---
                disable_events = df_detail[df_detail['EventType'] == 'DISABLE']
                enable_events = df_detail[df_detail['EventType'] == 'ENABLE']
                #-- plot the trend of disable and enable events over time ---
                results = []
                for _, d_row in disable_events.iterrows():
                    #-- find the closest enable event after the disable event ---
                    match_enable = enable_events[enable_events['CreateTime'] > d_row['CreateTime']]
                    if not match_enable.empty:
                        e_timestamp = match_enable['CreateTime'].iloc[0]
                        duration = e_timestamp - d_row['CreateTime']
                        results.append({
                            'Start(Diable)': d_row['CreateTime'],
                            'End(Enable)': e_timestamp,
                            'Duration': duration
                        })
                results_df = pd.DataFrame(results)
                if not results_df.empty:
                    results_df = results_df.sort_values(by='Duration', ascending=False)
                    longest_event = results_df.iloc[0]
                    st.error(f"Longest DISABLE: {longest_event['Duration']} (from {longest_event['Start(Diable)']})")
                
                    st.table(results_df)
                    # longest_idx = results_df['Duration'].idxmax()
                    # longest_duration = results_df.loc[longest_idx]

                    # st.error(f"Longest DISABLE duration for  {longest_duration['Duration']} (from {longest_duration['Start(Diable)']} to {longest_duration['End(Enable)']})")

                    # st.write("details of all DISABLE events and their corresponding ENABLE events:")
                    # st.table(results_df)
                else:
                    st.info("No DISABLE events found for the selected ERACKID.")
            else:
                st.warning("No data available for the selected ERACKID.")
    except Exception as e:
        st.error(f"An error occurred while fetching data in tab2: {e}")
        return pd.DataFrame()

def main():
    st.title("ERACK DISABLE Events Statistics and Analysis")

    try:
        engine = get_db_engine()
        #-- add a button to reset the charts---
        if st.button("Reset Charts"):
            if "erack_chart" in st.session_state:
                st.session_state["erack_chart"] = None
            st.rerun()  # 重新執行應用程式以重置狀態

        res = run_tab1_query(engine)
        
        # 這是為了方便你觀察點擊後的結構變化的 Debug 訊息
        # st.write("Debug - Click Data:", res)
        
        selected_id = None

        if res is not None:
            if isinstance(res, dict):
                # 關鍵修正：根據你的截圖，鍵值應該是 'chart_event'
                selected_id = res.get('chart_event') 
            elif isinstance(res, str):
                selected_id = res

        if selected_id:
            st.divider()
            # 確保傳進去的是乾淨的字串
            run_tab2_query(engine, str(selected_id)) 
        else:
            st.info("💡 請點擊上方的藍色長條圖柱子，系統將自動載入該設備的停用時間排序。")

    except Exception as e:
        st.error(f"An error occurred in the main function: {e}")

# def main():
    # st.title("ERACK DISABLE Events Statistics and  Analysis")

    # try:
    #     engine = get_db_engine()
    #     #-- 一個分頁但有互動式的寫法---
    #     res = run_tab1_query(engine)
    #     st.write("Debug - Click Data:", res)
    #     selected_id = None

    #     # 2. 解析 st_echarts 的回傳值
    #     if res is not None:
    #         if isinstance(res, dict):
    #             # 情況 A：回傳字典，通常 ID 在 'name' 或 'data' 鍵值中
    #             # 根據你的 events 設定，params.name 通常會對應到 'name'
    #             selected_id = res.get('name') or res.get('data')
    #         elif isinstance(res, str):
    #             # 情況 B：直接回傳字串
    #             selected_id = res

    #     # 3. 如果成功抓到 ID，才顯示下方的分析
    #     if selected_id:
    #         st.divider()
    #         # 傳入抓到的字串 ID (例如 'ERK-032')
    #         run_tab2_query(engine, str(selected_id)) 
    #     else:
    #         st.info("💡 請點擊上方的藍色長條圖柱子，系統將自動載入該設備的停用時間排序。")

    #     # if res is not None:
    #     #     if isinstance(res, dict):
    #     #         selected_id = res.get('data', None)  # 獲取點擊的數據名稱
    #     #     else:
    #     #         selected_id = res  # 如果直接返回字符串，則使用它作為選擇的ID
    #     #     if selected_id:
    #     #         st.divider()  # 添加分隔線
    #     #         run_tab2_query(engine, selected_id)
    #     #     else:
    #     #         st.warning("Please click on a bar in the chart to analyze the DISABLE events trend for that ERACKID.")
               


    #     # -- build tab objects 兩個分頁的寫法---
    #     # tab1, tab2 = st.tabs(["DISABLE Events Count", "DISABLE Events Trend"])
    #     # with tab1:
    #     #     df_count = run_tab1_query(engine)
    #     # with tab2:
    #     #     if not df_count.empty:
    #     #         run_tab2_query(engine, df_count['ErackID'])
    #     #     else:
    #     #         st.warning("No data available to analyze DISABLE events trend.")
    # except Exception as e:
    #     st.error(f"An error occurred in the main function: {e}")
    #     return
    
if __name__ == "__main__":
    main()