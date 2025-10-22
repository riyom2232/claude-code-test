# 제품 이미지 생성기 🖼️

Google Gemini API와 Vertex AI Imagen을 활용하여 제품 대표 이미지 1장을 분석하고, 블로그 리뷰용 이미지를 최대 10개까지 자동 생성하는 웹 애플리케이션입니다.

## 주요 기능 ✨

- **제품 이미지 업로드**: 드래그 앤 드롭 또는 파일 선택으로 간편한 업로드
- **AI 이미지 분석**: Google Gemini API를 통한 제품 자동 분석
  - 제품명, 카테고리, 주요 특징 파악
  - 색상, 스타일, 타겟 고객층 식별
  - 사용 사례 및 제품 설명 생성
- **AI 이미지 생성**: Vertex AI Imagen을 통한 실제 이미지 자동 생성 (최대 10개)
  - 블로그 리뷰에 최적화된 다양한 장면 생성
  - 한글 프롬프트 지원
  - 고품질 PNG 이미지 출력
- **쿠팡 파트너스 최적화**: 제품 리뷰 블로그 수익화에 바로 사용 가능

## 시작하기 🚀

### 1. 필수 요구사항

- Python 3.8 이상
- Google Gemini API 키 ([발급 받기](https://makersuite.google.com/app/apikey))
- Google Cloud Platform (GCP) 프로젝트 및 Vertex AI API 활성화
- GCP 서비스 계정 또는 Application Default Credentials 설정

### 2. 설치

```bash
# 저장소 클론
git clone https://github.com/riyom2232/claude-code-test.git
cd claude-code-test

# 가상 환경 생성 (선택사항이지만 권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 다음 정보 입력:
# GOOGLE_API_KEY=your_gemini_api_key
# GCP_PROJECT_ID=your_gcp_project_id
# GCP_LOCATION=us-central1
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json (선택사항)
```

**GCP 서비스 계정 설정 (권장)**

```bash
# GCP 콘솔에서 서비스 계정 생성 후 JSON 키 다운로드
# Vertex AI User 권한 부여 필요

# 환경 변수 설정
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account-key.json"
```

### 4. 실행

```bash
# Flask 앱 실행
python app.py
```

웹 브라우저에서 `http://localhost:5000` 접속

## 사용 방법 📝

1. **이미지 업로드**
   - 제품 대표 이미지를 업로드 영역에 드래그 앤 드롭하거나 클릭하여 선택
   - 지원 형식: JPG, PNG, WEBP (최대 16MB)

2. **AI 분석**
   - 업로드 즉시 Google Gemini가 이미지를 자동 분석
   - 제품 정보가 화면에 표시됨

3. **AI 이미지 생성**
   - 생성할 이미지 개수 선택 (1~10개)
   - "이미지 생성하기" 버튼 클릭
   - Vertex AI Imagen이 자동으로 블로그 리뷰용 이미지 생성
   - 생성된 이미지는 `generated/` 폴더에 PNG 형식으로 저장됨

4. **이미지 다운로드 및 활용**
   - 생성된 이미지를 다운로드하여 블로그에 바로 사용
   - 각 이미지마다 생성된 프롬프트도 함께 제공됨

## 프로젝트 구조 📁

```
claude-code-test/
├── app.py                 # Flask 메인 애플리케이션
├── requirements.txt       # Python 패키지 의존성
├── .env.example          # 환경 변수 예제
├── templates/
│   └── index.html        # 웹 UI
├── static/               # 정적 파일 (CSS, JS)
├── uploads/              # 업로드된 이미지 저장
└── generated/            # 생성된 이미지 저장
```

## 기술 스택 🛠️

- **Backend**: Flask (Python)
- **AI/ML**:
  - Google Gemini API (gemini-2.5-flash-image) - 이미지 분석 및 프롬프트 생성
  - Vertex AI Imagen (imagegeneration@006) - 이미지 생성
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **이미지 처리**: Pillow
- **클라우드**: Google Cloud Platform (Vertex AI)

## API 키 발급 방법 🔑

### 1. Google Gemini API 키

1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. Google 계정으로 로그인
3. "Create API Key" 클릭
4. 생성된 키를 복사하여 `.env` 파일에 입력

### 2. Google Cloud Platform 설정

1. [GCP Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. Vertex AI API 활성화:
   - API 및 서비스 > 라이브러리 > "Vertex AI API" 검색 > 사용 설정
4. 서비스 계정 생성:
   - IAM 및 관리 > 서비스 계정 > 서비스 계정 만들기
   - 역할: "Vertex AI User" 권한 부여
   - JSON 키 파일 다운로드
5. 프로젝트 ID를 `.env` 파일에 입력
6. JSON 키 파일 경로를 `GOOGLE_APPLICATION_CREDENTIALS` 환경변수에 설정

## 문제 해결 🔧

### API 키가 작동하지 않을 때

```bash
# .env 파일 확인
cat .env

# 환경 변수가 로드되는지 확인
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_API_KEY'))"
```

### 포트가 이미 사용 중일 때

```bash
# 다른 포트로 실행
# app.py의 마지막 줄을 수정: app.run(debug=True, host='0.0.0.0', port=5001)
```

## 라이선스 📄

MIT License

## 기여하기 🤝

이슈나 풀 리퀘스트는 언제나 환영합니다!

## 지원 💬

문제가 있거나 질문이 있으시면 이슈를 생성해주세요.
