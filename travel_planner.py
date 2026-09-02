# =========================================================
# A1-2 국내 여행지 추천 프로그램
# Gemini API + Kakao Local API를 활용한 CLI 프로그램
# =========================================================


# ---------------------------------------------------------
# 1. 필요한 라이브러리 불러오기
# ---------------------------------------------------------

# Google Gemini API를 사용하기 위한 라이브러리
from google import genai

# 파일 및 폴더 경로를 편리하게 다루기 위한 라이브러리
from pathlib import Path

# 프로그램을 종료할 때 사용하는 라이브러리
import sys

# 터미널에서 -date, --date 같은 입력값(argument)을 받기 위한 라이브러리
# argparse = argument + parse
import argparse

# 환경변수(.env에 저장된 API KEY)를 읽기 위한 라이브러리
import os

# JSON 문자열 ↔ Python 데이터 변환에 사용
import json

# Kakao REST API에 HTTP 요청을 보내기 위한 라이브러리
import requests

# 사용자가 입력한 날짜가 실제 날짜인지 검사하기 위해 사용
from datetime import datetime

# .env 파일 내용을 환경변수로 불러오기 위해 사용
from dotenv import load_dotenv


# =========================================================
# 2. 터미널에서 여행 날짜 입력받기
# =========================================================

# ArgumentParser 객체 생성
# 사용자가 터미널에서 입력한 값을 해석하는 역할
parser = argparse.ArgumentParser(
    description="국내 여행지 추천 프로그램"
)

# -date 또는 --date 옵션 추가
# required=True이므로 날짜를 입력하지 않으면 자동으로 오류 발생
parser.add_argument(
    "-date",
    "--date",
    required=True,
    help='여행 날짜를 "YYYY-MM-DD" 형식으로 입력하세요.'
)

# 실제 터미널 입력값을 분석(parse)하여 args에 저장
args = parser.parse_args()


# =========================================================
# 3. 날짜 형식 검증
# =========================================================

try:
    # 문자열을 실제 날짜(datetime)로 변환
    # 예: "2026-10-15" → 정상
    # 예: "2026-02-30" → 존재하지 않는 날짜이므로 ValueError 발생
    parsed_date = datetime.strptime(args.date, "%Y-%m-%d")

    # strptime은 일부 환경에서 2026-2-3처럼
    # 0이 빠진 입력도 받아들일 수 있으므로,
    # 다시 YYYY-MM-DD로 변환한 결과와 원래 입력을 비교한다.
    if parsed_date.strftime("%Y-%m-%d") != args.date:
        raise ValueError

except ValueError:
    # 날짜 형식이 틀렸거나 실제 존재하지 않는 날짜일 경우
    parser.error(
        '날짜가 올바르지 않습니다. 예: "2026-10-15"처럼 '
        '"YYYY-MM-DD" 형식의 실제 날짜를 입력하세요.'
    )


# =========================================================
# 4. .env 파일에서 API KEY 가져오기
# =========================================================

# .env 파일의 내용을 환경변수로 불러옴
load_dotenv()

# os.getenv()를 사용하여 환경변수에서 API KEY 가져오기
gemini_api_key = os.getenv("GEMINI_API_KEY")
kakao_api_key = os.getenv("KAKAO_REST_API_KEY")


# API KEY가 없는 경우 프로그램 실행 중단
if not gemini_api_key:
    print("오류: GEMINI_API_KEY가 설정되지 않았습니다.")
    print(".env 파일에 GEMINI_API_KEY를 설정해주세요.")
    sys.exit(1)

if not kakao_api_key:
    print("오류: KAKAO_REST_API_KEY가 설정되지 않았습니다.")
    print(".env 파일에 KAKAO_REST_API_KEY를 설정해주세요.")
    sys.exit(1)


# =========================================================
# 5. Gemini API 클라이언트 생성
# =========================================================

# 발급받은 Gemini API KEY를 사용하여 Gemini와 연결
client = genai.Client(api_key=gemini_api_key)


# =========================================================
# 6. Gemini에게 국내 여행지 추천 요청
# =========================================================

# Gemini에게 전달할 프롬프트
prompt = f"""
여행 날짜는 {args.date}입니다.

이 날짜에 국내 여행하기 좋은 도시 또는 여행 지역 한 곳을 추천해주세요.

서울특별시, 부산광역시처럼 범위가 매우 넓은 지역을 추천하는 경우에는
가능하면 실제 하루 여행 동선을 구성하기 좋은 세부 관광 지역을 추천해주세요.

예:
부산광역시 → 해운대, 광안리, 남포동
서울특별시 → 종로, 성수, 잠실
인천광역시 → 송도, 영종도, 월미도

반드시 아래 JSON 형식으로만 답해주세요.

{{
  "recommended_city": "도시 또는 세부 여행 지역명",
  "weather": "예상 날씨 설명",
  "events": ["행사1", "행사2"],
  "reason": "추천 이유를 2~4문장으로 작성"
}}

추가 설명이나 마크다운은 쓰지 말고 JSON만 반환해주세요.
"""


# ---------------------------------------------------------
# POST 방식 설명
# ---------------------------------------------------------
# Gemini의 generate_content()는 SDK가 대신 API 통신을 처리한다.
#
# 내부적으로는 Gemini의 generateContent REST API에
# 데이터를 보내서 새로운 결과를 "생성"해야 하기 때문에
# HTTP POST 방식의 요청이 사용된다.
#
# POST:
# 서버에 데이터(prompt 등)를 Request Body에 담아 보내고
# 서버가 이를 처리하도록 요청할 때 주로 사용한다.
#
# 우리는 requests.post()를 직접 쓰지 않고
# google-genai SDK의 generate_content()를 사용하기 때문에
# POST 요청 과정이 SDK 안에 숨겨져 있다.


try:
    gemini_response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

except Exception as e:
    # Gemini 서버, 네트워크, API KEY 등의 문제로
    # API 요청 자체가 실패한 경우
    print(f"오류: Gemini API 요청에 실패했습니다. ({e})")
    sys.exit(1)


# =========================================================
# 7. Gemini 응답을 JSON → Python 데이터로 변환
# =========================================================

# Gemini가 반드시 포함해야 하는 JSON 항목
required_keys = {
    "recommended_city",
    "weather",
    "events",
    "reason"
}


try:
    # response.text는 문자열이므로
    # json.loads()를 이용해 Python dictionary로 변환
    recommendation = json.loads(gemini_response.text)

    # JSON 자체는 정상이어도 필요한 항목이 빠질 수 있으므로 검사
    if not required_keys.issubset(recommendation.keys()):
        raise json.JSONDecodeError(
            "필수 JSON 항목이 없습니다.",
            gemini_response.text,
            0
        )

    # events는 과제 요구사항상 배열(list)이어야 함
    if not isinstance(recommendation["events"], list):
        raise json.JSONDecodeError(
            "events가 배열 형식이 아닙니다.",
            gemini_response.text,
            0
        )


except (json.JSONDecodeError, TypeError):
    # Gemini가 JSON 형식을 지키지 않은 경우 한 번만 다시 요청
    print("AI 응답 JSON 변환 실패 → 1회 재시도합니다.")

    retry_prompt = f"""
여행 날짜는 {args.date}입니다.

국내 여행하기 좋은 도시 또는 여행 지역 한 곳을 추천해주세요.

반드시 다른 설명 없이 아래 형식의 JSON만 반환해주세요.

{{
    "recommended_city": "도시 또는 세부 여행 지역명",
    "weather": "예상 날씨",
    "events": ["행사1", "행사2"],
    "reason": "추천 이유 2~4문장"
}}
"""

    try:
        # 이 호출 역시 Gemini API에 데이터를 전송하므로
        # SDK 내부에서는 POST 방식으로 요청된다.
        retry_response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=retry_prompt
        )

        recommendation = json.loads(retry_response.text)

        # 재시도 결과도 필수 항목 검사
        if not required_keys.issubset(recommendation.keys()):
            raise json.JSONDecodeError(
                "필수 JSON 항목이 없습니다.",
                retry_response.text,
                0
            )

        if not isinstance(recommendation["events"], list):
            raise json.JSONDecodeError(
                "events가 배열 형식이 아닙니다.",
                retry_response.text,
                0
            )

    except (json.JSONDecodeError, TypeError):
        print(
            "오류: 재시도 후에도 "
            "AI 응답을 올바른 JSON으로 변환하지 못했습니다."
        )
        sys.exit(1)

    except Exception as e:
        print(f"오류: Gemini API 재요청에 실패했습니다. ({e})")
        sys.exit(1)


# =========================================================
# 8. Gemini 추천 결과 확인
# =========================================================

print("추천 도시:", recommendation["recommended_city"])
print("예상 날씨:", recommendation["weather"])
print("행사:", recommendation["events"])
print("추천 이유:", recommendation["reason"])


# Gemini가 추천한 지역을 Kakao API 검색어에 사용
city = recommendation["recommended_city"]


# =========================================================
# 9. Kakao Local API로 추천 지역 맛집 검색
# =========================================================

# Kakao Local 키워드 검색 API 주소
url = "https://dapi.kakao.com/v2/local/search/keyword.json"


# HTTP Header
# Kakao REST API KEY를 Authorization 헤더에 담아 전송
headers = {
    "Authorization": f"KakaoAK {kakao_api_key}"
}


# GET 요청 시 URL 뒤에 붙어 전달될 Query Parameter
params = {
    "query": f"{city} 맛집",
    "size": 5
}


# ---------------------------------------------------------
# GET 방식 설명
# ---------------------------------------------------------
# 이번 Kakao API는 기존 장소 데이터를 "조회"하는 목적이다.
# 따라서 HTTP GET 방식을 사용한다.
#
# GET:
# 서버에 이미 존재하는 정보를 가져올 때 주로 사용한다.
#
# 아래 코드의 requests.get()이 실제 GET 요청이다.
#
# params에 들어있는 값은 실제 요청 시 대략 다음처럼 전달된다.
#
# ?query=해운대 맛집&size=5
#
# 즉,
# Gemini 결과 → city → Kakao GET 요청의 검색어
# 순서로 두 API가 연결된다.


# 맛집 정보를 저장할 리스트
restaurants = []

# API 실행 중 발생한 오류를 기록할 리스트
errors = []


try:
    # Kakao 서버에 GET 요청
    kakao_response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    # HTTP 상태 코드가 400, 401, 403, 500 등 오류라면
    # HTTPError를 발생시킨다.
    kakao_response.raise_for_status()

    # Kakao가 반환한 JSON을 Python dictionary로 변환
    kakao_data = kakao_response.json()

    # Kakao 검색 결과 documents를 하나씩 반복
    for place in kakao_data.get("documents", []):

        # 필요한 정보만 새로운 dictionary로 정리
        restaurant = {
            "name": place.get("place_name", ""),

            # 도로명 주소가 없으면 일반 지번 주소 사용
            "address": (
                place.get("road_address_name")
                or place.get("address_name", "")
            ),

            "category": place.get("category_name", ""),
            "url": place.get("place_url", ""),

            # Kakao x = 경도(longitude)
            "x": float(place["x"]) if place.get("x") else None,

            # Kakao y = 위도(latitude)
            "y": float(place["y"]) if place.get("y") else None
        }

        # 완성된 맛집 dictionary를 restaurants 리스트에 추가
        restaurants.append(restaurant)


    # 검색 결과가 한 개 이상 존재할 경우
    if restaurants:
        print("맛집 검색 결과 개수:", len(restaurants))

    # API 요청은 성공했지만 검색 결과가 0개인 경우
    else:
        print("맛집 검색 결과: 데이터 없음")


# ---------------------------------------------------------
# Kakao HTTP 오류 처리
# 예: 401 인증 실패, 403 권한 문제, 500 서버 오류 등
# ---------------------------------------------------------
except requests.exceptions.HTTPError as e:
    error_message = f"Kakao API HTTP 오류: {e}"

    # errors 리스트에 오류 기록
    errors.append(error_message)

    print(error_message)
    print("맛집 정보 없이 여행 리포트를 계속 생성합니다.")


# ---------------------------------------------------------
# Kakao 요청 자체의 오류 처리
# 예: 인터넷 연결 실패, timeout 등
# ---------------------------------------------------------
except requests.exceptions.RequestException as e:
    error_message = f"Kakao API 요청 오류: {e}"

    errors.append(error_message)

    print(error_message)
    print("맛집 정보 없이 여행 리포트를 계속 생성합니다.")


# ---------------------------------------------------------
# Kakao가 JSON이 아닌 잘못된 응답을 반환했을 경우
# ---------------------------------------------------------
except (ValueError, KeyError) as e:
    error_message = f"Kakao API 응답 처리 오류: {e}"

    errors.append(error_message)

    print(error_message)
    print("맛집 정보 없이 여행 리포트를 계속 생성합니다.")


# =========================================================
# 10. 원본 데이터(JSON) 만들기
# =========================================================

result_data = {
    "recommendation": recommendation,
    "restaurants": restaurants,
    "errors": errors
}


# =========================================================
# 11. results 폴더 생성
# =========================================================

results_dir = Path("results")

# exist_ok=True:
# results 폴더가 이미 있어도 오류를 발생시키지 않는다.
results_dir.mkdir(exist_ok=True)


# =========================================================
# 12. 원본 JSON 파일 저장
# =========================================================

json_path = results_dir / f"{args.date}_data.json"


with open(json_path, "w", encoding="utf-8") as f:

    # ensure_ascii=False
    # → 한글을 \uXXXX 형태가 아니라 그대로 저장

    # indent=2
    # → 사람이 읽기 편하게 들여쓰기해서 저장
    json.dump(
        result_data,
        f,
        ensure_ascii=False,
        indent=2
    )


print("JSON 저장 완료:", json_path)


# =========================================================
# 13. 최종 Markdown 여행 리포트용 프롬프트 만들기
# =========================================================

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

맛집 정보가 "데이터 없음"인 경우
임의로 맛집을 만들어내지 말고
추천 맛집 항목에 "데이터 없음"이라고 작성해주세요.

오류 정보가 "없음"이면
오류 정보 항목에는 "없음"이라고 작성해주세요.

오류가 있으면 제공된 오류 내용만 간단히 정리해주세요.
"""


# =========================================================
# 14. Gemini API로 최종 Markdown 리포트 생성
# =========================================================

try:
    # 이 generate_content() 역시 SDK 내부에서
    # Gemini generateContent API에 POST 요청을 보낸다.
    report_response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=report_prompt
    )

    # Gemini가 만들어준 Markdown 문자열
    report_markdown = report_response.text


except Exception as e:
    # 최종 리포트 생성 과정에서 Gemini API가 실패한 경우
    error_message = f"Gemini 리포트 생성 오류: {e}"
    errors.append(error_message)

    print(error_message)

    # Gemini 리포트 생성 실패 시에도
    # 최소한의 결과 파일을 남길 수 있도록 기본 Markdown 생성
    restaurant_text = (
        "\n".join(
            f"- {restaurant['name']} / {restaurant['address']}"
            for restaurant in restaurants
        )
        if restaurants
        else "데이터 없음"
    )

    report_markdown = f"""# {args.date} 국내 여행 추천 리포트

## 추천 지역 및 추천 이유
{recommendation["recommended_city"]}

{recommendation["reason"]}

## 예상 날씨
{recommendation["weather"]}

## 주요 행사
{chr(10).join(f"- {event}" for event in recommendation["events"])}

## 추천 맛집
{restaurant_text}

## 하루 여행 일정
Gemini API 오류로 자동 일정을 생성하지 못했습니다.

## 오류 정보
{error_message}
"""


# =========================================================
# 15. 최종 여행 리포트 터미널 출력
# =========================================================

print("\n===== 최종 여행 리포트 =====")
print(report_markdown)


# =========================================================
# 16. Markdown 파일 저장
# =========================================================

markdown_path = results_dir / f"{args.date}_travel_plan.md"


with open(markdown_path, "w", encoding="utf-8") as f:
    f.write(report_markdown)


print("Markdown 저장 완료:", markdown_path)


# =========================================================
# 17. 최종 errors 내용을 JSON에도 다시 반영
# =========================================================
# 최종 Gemini 리포트 생성 단계에서 오류가 발생하면
# errors 리스트가 추가될 수 있다.
#
# 따라서 마지막에 JSON 파일을 한 번 더 저장하여
# 최종 오류 정보까지 JSON에 반영한다.

result_data["errors"] = errors

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(
        result_data,
        f,
        ensure_ascii=False,
        indent=2
    )