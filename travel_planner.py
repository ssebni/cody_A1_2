from google import genai
from pathlib import Path
import sys 
import argparse
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

parser = argparse.ArgumentParser(
    description="국내 여행지 추천 프로그램"
)

parser.add_argument(
    "-date",
    "--date",
    required=True,
    help='여행 날짜를 "YYYY-MM-DD" 형식으로 입력하세요.'
)

args = parser.parse_args()

load_dotenv()

# 날짜 형식 검증
try:
    datetime.strptime(args.date, "%Y-%m-%d")
except ValueError:
    parser.error('날짜 형식이 올바르지 않습니다. "YYYY-MM-DD" 형식으로 입력하세요.')

gemini_api_key = os.getenv("GEMINI_API_KEY")
kakao_api_key = os.getenv("KAKAO_REST_API_KEY")

if not gemini_api_key:
    print("오류: GEMINI_API_KEY가 설정되지 않았습니다.")
    print(".env 파일에 GEMINI_API_KEY를 설정해주세요.")
    sys.exit(1)

if not kakao_api_key:
    print("오류: KAKAO_REST_API_KEY가 설정되지 않았습니다.")
    print(".env 파일에 KAKAO_REST_API_KEY를 설정해주세요.")
    sys.exit(1)

client = genai.Client(api_key=gemini_api_key)

prompt = f"""
여행 날짜는 {args.date}입니다.

이 날짜에 국내 여행하기 좋은 도시 한 곳을 추천해주세요.

반드시 아래 JSON 형식으로만 답해주세요.

{{
  "recommended_city": "도시명",
  "weather": "예상 날씨 설명",
  "events": ["행사1", "행사2"],
  "reason": "추천 이유를 2~4문장으로 작성"
}}

추가 설명이나 마크다운은 쓰지 말고 JSON만 반환해주세요.
"""

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=prompt
)

try:
    recommendation = json.loads(response.text)

except json.JSONDecodeError:
    print("AI 응답 JSON 변환 실패 → 1회 재시도합니다.")

    retry_response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=f"""
{args.date}에 국내 여행하기 좋은 도시 한 곳을 추천해주세요.

반드시 다른 설명 없이 JSON만 반환해주세요.

형식:
{{
    "recommended_city": "도시명",
    "weather": "예상 날씨",
    "events": ["행사1", "행사2"],
    "reason": "추천 이유 2~4문장"
}}
"""
    )

    try:
        recommendation = json.loads(retry_response.text)

    except json.JSONDecodeError:
        print("오류: 재시도 후에도 AI 응답을 JSON으로 변환하지 못했습니다.")
        sys.exit(1)

print("추천 도시:", recommendation["recommended_city"])
print("예상 날씨:", recommendation["weather"])
print("행사:", recommendation["events"])
print("추천 이유:", recommendation["reason"])

city = recommendation["recommended_city"]

url = "https://dapi.kakao.com/v2/local/search/keyword.json"

headers = {
    "Authorization": f"KakaoAK {kakao_api_key}"
}

params = {
    "query": f"{city} 맛집",
    "size": 5
}

restaurants = []
errors = []

try:
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    kakao_data = response.json()

    for place in kakao_data["documents"]:
        restaurant = {
            "name": place["place_name"],
            "address": place["road_address_name"] or place["address_name"],
            "category": place["category_name"],
            "url": place["place_url"],
            "x": float(place["x"]),
            "y": float(place["y"])
        }

        restaurants.append(restaurant)

    if restaurants:
        print("맛집 검색 결과 개수:", len(restaurants))
    else:
        print("맛집 검색 결과: 데이터 없음")

except requests.exceptions.HTTPError as e:
    error_message = f"Kakao API HTTP 오류: {e}"
    errors.append(error_message)
    print(error_message)
    print("맛집 정보 없이 여행 리포트를 계속 생성합니다.")

except requests.exceptions.RequestException as e:
    error_message = f"Kakao API 요청 오류: {e}"
    errors.append(error_message)
    print(error_message)
    print("맛집 정보 없이 여행 리포트를 계속 생성합니다.")

result_data = {
    "recommendation": recommendation,
    "restaurants": restaurants,
    "errors": errors
}

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

json_path = results_dir / f"{args.date}_data.json"

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(result_data, f, ensure_ascii=False, indent=2)

print("JSON 저장 완료:", json_path)

report_prompt = f"""
다음 데이터를 바탕으로 국내 여행 리포트를 작성해주세요.

여행 날짜:
{args.date}

여행지 추천 정보:
{json.dumps(recommendation, ensure_ascii=False)}

맛집 정보:
{json.dumps(restaurants, ensure_ascii=False) if restaurants else "데이터 없음"}

오류 정보:
{json.dumps(errors, ensure_ascii=False) if errors else "없음"}

반드시 Markdown 형식으로 작성하고 다음 내용을 포함해주세요.

# {args.date} 국내 여행 추천 리포트

## 추천 지역 및 추천 이유
## 예상 날씨
## 주요 행사
## 추천 맛집
## 하루 여행 일정
- 오전
- 오후
- 저녁
## 오류 정보
맛집 정보는 제공된 Kakao 검색 결과만 사용해주세요.
맛집 정보가 "데이터 없음"인 경우 임의로 맛집을 만들어내지 말고,
추천 맛집 항목에 "데이터 없음"이라고 작성해주세요.
오류 정보가 "없음"이면 오류 정보 항목에는 "없음"이라고 작성해주세요.
오류가 있으면 제공된 오류 내용만 간단히 정리해주세요.
"""

report_response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=report_prompt
)

report_markdown = report_response.text

print("\n===== 최종 여행 리포트 =====")
print(report_markdown)

markdown_path = results_dir / f"{args.date}_travel_plan.md"

with open(markdown_path, "w", encoding="utf-8") as f:
    f.write(report_markdown)

print("Markdown 저장 완료:", markdown_path)