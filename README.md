# A1-2 국내 여행지 추천 프로그램

## 1. 프로젝트 소개

여행 날짜를 입력하면 Gemini API가 국내 여행지를 추천하고,
Kakao Local API를 이용해 해당 지역의 맛집 정보를 검색한 뒤
최종 여행 리포트를 Markdown 파일로 생성하는 CLI 프로그램입니다.

## 2. 주요 기능

- 여행 날짜 입력 및 형식 검증
- Gemini API를 이용한 국내 여행지 추천
- 추천 결과를 JSON 형식으로 처리
- Kakao Local API를 이용한 맛집 검색
- 맛집 정보 5개 조회
- API 오류 발생 시 오류 내용을 기록하고 프로그램 계속 실행
- 원본 JSON 결과 저장
- 최종 Markdown 여행 리포트 저장

## 3. 실행 환경

- Python 3.10 이상

필요한 패키지는 `requirements.txt`에 정리되어 있습니다.

설치:

    pip install -r requirements.txt

## 4. API 키 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래와 같이 설정합니다.

    GEMINI_API_KEY=본인의_Gemini_API_키
    KAKAO_REST_API_KEY=본인의_Kakao_REST_API_키

실제 API 키는 GitHub에 업로드하지 않습니다.

`.gitignore`에 아래 항목을 추가합니다.

    .env
    .venv/

## 5. 실행 방법

    python3 travel_planner.py -date "2026-10-15"

또는:

    python3 travel_planner.py --date "2026-10-15"

날짜 형식은 반드시 `YYYY-MM-DD` 형식이어야 합니다.

잘못된 예시:

    python3 travel_planner.py -date "20261015"

## 6. 실행 흐름

1. 사용자가 여행 날짜를 입력합니다.
2. Gemini API가 추천 도시, 예상 날씨, 행사, 추천 이유를 JSON으로 반환합니다.
3. 추천 도시를 이용해 Kakao Local API에서 맛집을 검색합니다.
4. 검색된 맛집 정보를 JSON 데이터에 저장합니다.
5. Gemini API가 최종 Markdown 여행 리포트를 작성합니다.
6. 결과 파일을 `results/` 폴더에 저장합니다.

## 7. 결과 파일

실행 후 `results/` 폴더에 다음 파일이 생성됩니다.

    results/
    ├── YYYY-MM-DD_data.json
    └── YYYY-MM-DD_travel_plan.md

### JSON 파일

다음 정보를 포함합니다.

- 여행지 추천 정보
- 맛집 정보
- API 오류 정보

### Markdown 파일

다음 내용을 포함합니다.

- 추천 지역 및 추천 이유
- 예상 날씨
- 주요 행사
- 추천 맛집
- 오전 / 오후 / 저녁 여행 일정
- 오류 정보

## 8. 오류 처리

- Gemini 응답을 JSON으로 변환하지 못한 경우 1회 재시도합니다.
- Kakao API 요청 실패 시 오류 내용을 `errors`에 기록합니다.
- Kakao API가 실패하거나 검색 결과가 없더라도 여행 리포트 생성은 계속 진행합니다.
- 맛집 정보가 없는 경우 최종 리포트에 `데이터 없음`으로 표시합니다.

## 9. API 키 보안

API 키는 코드에 직접 작성하지 않고 `.env` 파일에서 불러옵니다.

`.env` 파일은 `.gitignore`에 포함하여 GitHub에 업로드되지 않도록 관리합니다.

API 키가 외부에 노출된 경우 기존 키를 폐기하고 새 키를 발급하는 것이 안전합니다.