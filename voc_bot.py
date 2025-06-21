from google_play_scraper import reviews as gp_reviews
from app_store_web_scraper import AppStoreEntry
from datetime import datetime, timedelta
import pandas as pd
import openai
import time
import base64
import requests
import os
import json

#변수
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)
end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
confluence_api_token = os.environ.get("CONFLUENCE_API_TOKEN")
confluence_api_user = os.environ.get("CONFLUENCE_API_USER")
space_key = 'CSO'
parent_page_id = '619544652'
title = "자동 분석 리포트 샘플_" + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

## 이즐충전소 aos
google_app_id = 'com.locam.cashbeecharge'
result, _ = gp_reviews(
    google_app_id,
    lang='ko',
    country='kr',
    count=500
)
data_google = []
for r in result:
    data_google.append([
        '자사',
        '이즐충전소',       # 앱명칭
        'android',       # OS
        r['at'].strftime('%Y-%m-%d'),  # 작성일
        r.get('reviewCreatedVersion', ''),
        r.get('title', ''),
        r['content'],
        r['score']
    ])
df_google_c = pd.DataFrame(data_google, columns=['구분', '앱명칭', 'os', '작성일', '버전', '리뷰 제목', '리뷰 내용', '평점'])

## 모바일이즐
google_app_id = 'com.ebcard.cashbee3'
result, _ = gp_reviews(
    google_app_id,
    lang='ko',
    country='kr',
    count=500
)
data_google = []
for r in result:
    data_google.append([
        '자사',
        '모바일이즐',       # 앱명칭
        'android',       # OS
        r['at'].strftime('%Y-%m-%d'),  # 작성일
        r.get('reviewCreatedVersion', ''),
        r.get('title', ''),
        r['content'],
        r['score']
    ])
df_google_m = pd.DataFrame(data_google, columns=['구분', '앱명칭', 'os', '작성일', '버전', '리뷰 제목', '리뷰 내용', '평점'])

## 이즐충전소 ios
app = AppStoreEntry(app_id=1470361790, country="kr")
reviews = list(app.reviews(limit=500))
data_apple = []
for r in reviews:
    review_date = r.date.strftime('%Y-%m-%d') if hasattr(r, "date") and r.date else ''
    data_apple.append([
        '자사',
        '이즐충전소',         # 앱명칭
        'ios',              # OS
        review_date,        # 작성일
        '',                 # 버전(웹 스크래핑은 없음)
        r.title or '',
        r.review or '',
        r.rating
    ])
df_apple = pd.DataFrame(data_apple, columns=['구분', '앱명칭', 'os', '작성일', '버전', '리뷰 제목', '리뷰 내용', '평점'])

## 모바일티머니
google_app_id = 'com.lgt.tmoney'
result, _ = gp_reviews(
    google_app_id,
    lang='ko',
    country='kr',
    count=500
)
data_google = []
for r in result:
    data_google.append([
        '경쟁사',
        '모바일티머니',       # 앱명칭
        'android',       # OS
        r['at'].strftime('%Y-%m-%d'),  # 작성일
        r.get('reviewCreatedVersion', ''),
        r.get('title', ''),
        r['content'],
        r['score']
    ])
df_google_t = pd.DataFrame(data_google, columns=['구분', '앱명칭', 'os', '작성일', '버전', '리뷰 제목', '리뷰 내용', '평점'])

## 모바일티머니 ios
app = AppStoreEntry(app_id=1519907149, country="kr")
reviews = list(app.reviews(limit=500))
data_apple = []
for r in reviews:
    review_date = r.date.strftime('%Y-%m-%d') if hasattr(r, "date") and r.date else ''
    data_apple.append([
        '경쟁사',
        '모바일티머니',         # 앱명칭
        'ios',              # OS
        review_date,        # 작성일
        '',                 # 버전(웹 스크래핑은 없음)
        r.title or '',
        r.review or '',
        r.rating
    ])
df_apple_t = pd.DataFrame(data_apple, columns=['구분', '앱명칭', 'os', '작성일', '버전', '리뷰 제목', '리뷰 내용', '평점'])

#합치기
df_all = pd.concat([df_google_m, df_google_c, df_apple, df_google_t, df_apple_t], ignore_index=True)

#기간 필터
start_date_dt = pd.to_datetime(start_date)
end_date_dt = pd.to_datetime(end_date)
df_all['작성일'] = pd.to_datetime(df_all['작성일'], errors='coerce')
df_all = df_all[(df_all['작성일'] >= start_date_dt) & (df_all['작성일'] <= end_date_dt)]

# 리뷰 합치기 (제목,내용)
df_all['리뷰 텍스트'] = df_all['리뷰 제목'].fillna('') + ' ' + df_all['리뷰 내용'].fillna('')
df_all = df_all.drop(['리뷰 제목', '리뷰 내용'], axis=1)

# 반응(긍정/부정) 칼럼 추가
df_all['반응'] = df_all['평점'].apply(lambda x: '긍정' if x >= 3 else '부정')
df_all['카테고리'] = ''

df_all = df_all[['구분', '앱명칭', 'os', '작성일', '버전', '리뷰 텍스트', '평점', '반응', '카테고리']]
df_filtered = df_all[df_all['평점'] <= 2].copy()

categories = """
카테고리명 | 포함 사례/키워드
---------|---------------------------------------------------------------------
앱 접속 오류 | 튕김, 접속장애, 강제종료, 멈춤, 로딩 무한, 빈화면 등
인식/등록/태깅/발급 | 카드 등록/조회 실패, 카드 미인식, 태그 실패, 발행, 발급, 승하차 오류, NFC 문제 등
충전/잔액/결제/환불 | 충전 실패/지연, 잔액 오류, 결제/환불 실패·지연, 이중 결제, 충전 미완료, 수수료 불만, 환불 지연 등
기기 호환/업데이트 | 단말기 호환성 문제, 특정 기기에서 오류, OS/앱 업데이트 후 문제, 유심 문제, 앱 버전 문제, 신규 업데이트 적용 후 오류 발생 등
고객센터/문의/CS | 고객센터 연결 안 됨, 문의/상담 지연, 답변 없음, 불친절, 민원 처리 미흡, CS센터 전화 안 됨, 온라인 문의 답변 지연, 고객 응대 불만 등
UI/UX/이용불편/인증 | 화면 구성 불편, 버튼/메뉴 찾기 어려움, 디자인 불만, 인증 실패, 본인 인증 반복 요구, 절차 과다 등
알림/푸시/공지 | 알림이 오지 않음, 푸시 미수신, 공지사항 미노출, 이벤트/공지 알림 지연, 불필요한 알림, 알림 설정 문제 등
기타 | 위 항목에 포함되지 않는 기타 문제, 기타 건의사항, 단순 부정, 앱 전반에 대한 의견 등
"""

#지피티가 카테고리 분류해서 넣기
def classify_with_gpt(text):
    prompt = f"""
아래는 앱 리뷰입니다.

리뷰: "{text}"

아래 표의 카테고리와 예시 키워드를 참고하여, 반드시 가장 가까운 카테고리명 한 개만 선택하십시오.
반드시 다음 규칙을 지키세요:
- 아래 8개 카테고리 중 하나만 골라서, 카테고리명만 정확하게 출력하세요.
- 각 카테고리명 옆의 예시 키워드를 참고해 근접한 카테고리를 선택하세요.
- 단, 의미가 명확하지 않거나, 내용이 없는 단순 요청·욕설·불평은 '기타'로 분류하세요.
- 오직 카테고리명만 출력하세요. (설명, 번호 등 금지)

{categories}

"""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0
    )
    return response.choices[0].message.content.strip()

#분류 적용
for idx, row in df_filtered.iterrows():
    review_text = row['리뷰 텍스트'][:100]
    try:
        category = classify_with_gpt(review_text)
    except Exception as e:
        print(f"예외 발생: {e}")
        category = "기타"
    df_filtered.at[idx, '카테고리'] = category
    time.sleep(1.2)


#원본 df_all에 결과 반영
df_all.loc[df_filtered.index, '카테고리'] = df_filtered['카테고리']

summary = []

for company in ['자사', '경쟁사']:
    df_sub = df_all[df_all['구분'] == company]
    review_count = len(df_sub)
    positive = (df_sub['반응'] == '긍정').sum()
    negative = (df_sub['반응'] == '부정').sum()
    positive_ratio = round(negative / review_count * 100, 1) if review_count > 0 else 0
    avg_score = round(df_sub['평점'].mean(), 2) if review_count > 0 else 0
    summary.append([company, review_count, positive, negative, positive_ratio, avg_score])

# 2. 데이터프레임으로 변환
summary_df = pd.DataFrame(summary, columns=['구분', '리뷰수', '긍정', '부정', '부정비율', '평균평점'])

# [1] 데이터 저장
df_all.to_csv('df_all.csv', index=False, encoding='utf-8-sig')
csv_file_path = 'df_all.csv'

# [2] 자사/경쟁사별 리뷰·평점 요약표
summary = []
for company in ['자사', '경쟁사']:
    df_sub = df_all[df_all['구분'] == company]
    review_count = len(df_sub)
    positive = (df_sub['반응'] == '긍정').sum()
    negative = (df_sub['반응'] == '부정').sum()
    negative_ratio = round(negative / review_count * 100, 1) if review_count > 0 else 0
    avg_score = round(df_sub['평점'].mean(), 2) if review_count > 0 else 0
    summary.append([company, review_count, positive, negative, negative_ratio, avg_score])

summary_df = pd.DataFrame(summary, columns=['구분', '리뷰수', '긍정', '부정', '부정비율', '평균평점'])

# [3] 카테고리별 부정 리뷰 분포표
df_neg = df_all[df_all['반응'] == '부정']
category_table = df_neg.pivot_table(
    index='카테고리',
    columns='구분',
    values='리뷰 텍스트',
    aggfunc='count',
    fill_value=0
).reset_index()
category_table.columns.name = None
total_ja = category_table['자사'].sum()
total_comp = category_table['경쟁사'].sum()
category_table['비중(자사)'] = (category_table['자사'] / total_ja * 100).round(2)
category_table['비중(경쟁사)'] = (category_table['경쟁사'] / total_comp * 100).round(2)
category_table = category_table[['카테고리', '자사', '비중(자사)', '경쟁사', '비중(경쟁사)']]
category_order = [
    "앱 접속 오류", "인식/등록/태깅/발급", "충전/잔액/결제/환불",
    "기기 호환/업데이트", "고객센터/문의/CS",
    "UI/UX/이용불편/인증", "알림/푸시/공지", "기타"
]
category_table['카테고리'] = pd.Categorical(category_table['카테고리'], categories=category_order, ordered=True)
category_table = category_table.sort_values('카테고리')

# [4] HTML 변환 (컨플루언스 본문)
summary_html = summary_df.to_html(index=False, border=1)
category_html = category_table.to_html(index=False, border=1)

# [5] 주요 인사이트(gpt_anal) 생성: 최근 20개 리뷰만 요약 예시 (실무에서는 더 많은 row로 확장 가능)
review_texts = "\n".join(df_filtered.sort_values('작성일', ascending=False)['리뷰 텍스트'])

gpt_prompt = f"""아래는 앱 리뷰 데이터 일부입니다.

{review_texts}

이 리뷰 데이터를 참고해 아래 양식에 맞게 요약해주세요.

- 주요 긍정 포인트 (3줄 이내)
- 주요 개선 필요점 (3줄 이내)
- 인사이트/트렌드 (3줄 이내)

한글로 간단명료하게 작성해 주세요.
"""

# GPT API 호출
response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": "너는 데이터 분석가야."},
        {"role": "user", "content": gpt_prompt}
    ],
    max_tokens=512,
    temperature=0.5,
)
gpt_anal_text = response.choices[0].message.content.strip()
gpt_anal = f"<pre>{gpt_anal_text}</pre>"

# [6] body_html에 gpt_anal 삽입
body_html = f"""
<h2>1. 리뷰/평점 요약표</h2>
{summary_html}
<br>
<h2>2. 카테고리별 부정 리뷰 분포</h2>
{category_html}
<br>
<h2>3. 주요 인사이트</h2>
{gpt_anal}
<br>
<h2>[첨부] 아래 첨부파일(df_all.csv) 다운로드</h2>
<br>
"""

# [7] Confluence 페이지 생성
confluence_domain = 'myezl.atlassian.net'


headers = {
    'Authorization': 'Basic ' + base64.b64encode(f'{api_user}:{api_token}'.encode()).decode(),
    'Content-Type': 'application/json'
}
base_url = f'https://{confluence_domain}/wiki/rest/api/content/'

page_data = {
    "type": "page",
    "title": title,
    "ancestors": [{"id": parent_page_id}],
    "space": {"key": space_key},
    "body": {
        "storage": {
            "value": body_html,
            "representation": "storage"
        }
    }
}
response = requests.post(base_url, headers=headers, json=page_data)
assert response.status_code in [200, 201], "페이지 생성 실패: " + response.text
new_page_id = response.json()['id']
print("페이지 생성 완료:", new_page_id)

# [8] 첨부파일 업로드 (sleep 2초 후)
time.sleep(2)
attach_url = f'https://{confluence_domain}/wiki/rest/api/content/{new_page_id}/child/attachment'
attach_headers = {
    'Authorization': 'Basic ' + base64.b64encode(f'{api_user}:{api_token}'.encode()).decode(),
    'X-Atlassian-Token': 'no-check'
}
with open(csv_file_path, 'rb') as f:
    files = {'file': (os.path.basename(csv_file_path), f, 'text/csv')}
    attach_response = requests.post(attach_url, headers=attach_headers, files=files)

print("API 응답:", attach_response.status_code)
print(attach_response.text)

assert attach_response.status_code in [200, 201], "첨부파일 업로드 실패: " + attach_response.text
print("첨부파일 업로드 완료")

# [9] 본문에 다운로드 링크 PATCH
download_url = f"https://{confluence_domain}/wiki/download/attachments/{new_page_id}/df_all.csv"
patch_url = f'https://{confluence_domain}/wiki/rest/api/content/{new_page_id}'
patch_headers = headers
patch_data = {
    "version": {"number": 2},
    "title": title,
    "type": "page",
    "body": {
        "storage": {
            "value": body_html + f'<br><a href="{download_url}">df_all.csv 다운로드</a><br>',
            "representation": "storage"
        }
    }
}
patch_response = requests.put(patch_url, headers=patch_headers, json=patch_data)
print("본문에 다운로드 링크 추가 완료:", patch_response.status_code)