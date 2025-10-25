"""
제품 이미지 생성 웹 애플리케이션
Google Gemini 2.5 Flash Image API를 활용하여 제품 이미지를 분석하고 관련 이미지를 생성합니다.
"""

import os
import base64
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import google.generativeai as genai
from google import genai as genai_client
from google.genai import types
from PIL import Image
import io
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

app = Flask(__name__)
CORS(app)  # CORS 활성화
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}

# 폴더 생성
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['GENERATED_FOLDER']).mkdir(exist_ok=True)

# Google Gemini API 설정
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def allowed_file(filename):
    """허용된 파일 확장자 체크"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def analyze_product_image(image_path):
    """
    Gemini API를 사용하여 제품 이미지 분석
    """
    if not GOOGLE_API_KEY:
        error_msg = "GOOGLE_API_KEY가 설정되지 않았습니다."
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)

    try:
        # Gemini Pro Vision 모델 사용
        print(f"[DEBUG] 분석 모델 초기화: gemini-2.5-flash-image")
        model = genai.GenerativeModel('gemini-2.5-flash-image')

        # 이미지 로드
        print(f"[DEBUG] 이미지 로드 중: {image_path}")
        img = Image.open(image_path)
        print(f"[DEBUG] 이미지 크기: {img.size}")
    except Exception as e:
        print(f"[ERROR] 이미지 로드 실패: {str(e)}")
        raise

    # 이미지 분석 프롬프트
    prompt = """
    이 제품 이미지를 자세히 분석해주세요.

    다음 정보를 JSON 형식으로 제공해주세요:
    {
        "product_name": "제품명",
        "category": "카테고리",
        "key_features": ["특징1", "특징2", "특징3"],
        "color": "주요 색상",
        "style": "스타일 (모던, 클래식 등)",
        "target_audience": "타겟 고객층",
        "use_cases": ["사용 사례 1", "사용 사례 2", "사용 사례 3"],
        "description": "제품에 대한 상세 설명 (2-3문장)"
    }

    응답은 반드시 유효한 JSON 형식으로만 작성해주세요.
    """

    print(f"[DEBUG] 이미지 분석 API 호출 중...")
    try:
        response = model.generate_content([prompt, img])
        print(f"[DEBUG] 분석 응답 수신 완료")
    except Exception as e:
        print(f"[ERROR] 이미지 분석 API 호출 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    # JSON 파싱
    try:
        # 응답에서 JSON 추출 (마크다운 코드 블록 제거)
        response_text = response.text.strip()
        print(f"[DEBUG] 응답 텍스트 길이: {len(response_text)}")
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        analysis = json.loads(response_text.strip())
        print(f"[DEBUG] JSON 파싱 성공")
    except json.JSONDecodeError as e:
        # JSON 파싱 실패 시 기본값 반환
        print(f"[WARNING] JSON 파싱 실패, 기본값 사용: {str(e)}")
        print(f"[DEBUG] 원본 응답: {response.text[:500]}")
        analysis = {
            "product_name": "분석된 제품",
            "category": "일반 제품",
            "key_features": ["고품질", "실용적", "스타일리시"],
            "color": "다양한 색상",
            "style": "모던",
            "target_audience": "일반 소비자",
            "use_cases": ["일상 사용", "선물용", "실용적 용도"],
            "description": response.text[:200]
        }

    return analysis


def generate_image_prompts(analysis, num_images=10):
    """
    제품 분석 결과를 바탕으로 다양한 이미지 생성 프롬프트 생성
    """
    if not GOOGLE_API_KEY:
        error_msg = "GOOGLE_API_KEY가 설정되지 않았습니다."
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)

    print(f"[DEBUG] 프롬프트 생성 모델 초기화")
    model = genai.GenerativeModel('gemini-2.5-flash-image')

    prompt = f"""
    다음 제품 정보를 바탕으로 블로그 리뷰용 이미지 생성을 위한 {num_images}개의 다양한 장면/시나리오를 만들어주세요.

    제품 정보:
    - 제품명: {analysis['product_name']}
    - 카테고리: {analysis['category']}
    - 특징: {', '.join(analysis['key_features'])}
    - 스타일: {analysis['style']}
    - 타겟 고객: {analysis['target_audience']}
    - 사용 사례: {', '.join(analysis['use_cases'])}

    요구사항:
    1. 각 장면은 제품의 다른 측면이나 사용 상황을 보여줘야 합니다
    2. 블로그 리뷰에 적합한 실용적인 장면들
    3. 라이프스타일, 디테일 샷, 사용 장면, 패키징 등 다양하게 구성

    JSON 형식으로 응답:
    {{
        "prompts": [
            {{"title": "장면 제목", "description": "이미지 생성 프롬프트 (한글, 자세하고 구체적으로)"}},
            ...
        ]
    }}
    """

    print(f"[DEBUG] 프롬프트 생성 API 호출 중...")
    try:
        response = model.generate_content(prompt)
        print(f"[DEBUG] 프롬프트 생성 응답 수신 완료")
    except Exception as e:
        print(f"[ERROR] 프롬프트 생성 API 호출 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

    try:
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        prompts_data = json.loads(response_text.strip())
        print(f"[DEBUG] 프롬프트 JSON 파싱 성공 - {len(prompts_data['prompts'])}개 생성")
        return prompts_data['prompts'][:num_images]
    except (json.JSONDecodeError, KeyError) as e:
        # 기본 프롬프트 생성
        print(f"[WARNING] 프롬프트 JSON 파싱 실패, 기본 프롬프트 사용: {str(e)}")
        return [
            {"title": f"제품 사용 장면 {i+1}", "description": f"{analysis['product_name']}을(를) 사용하는 모습"}
            for i in range(num_images)
        ]


def generate_images_with_gemini(analysis, prompts, image_path):
    """
    Gemini 2.5 Flash Image API를 사용하여 실제 이미지 생성
    통일된 응답 스키마: {"status":"ok|error", "type":"base64|url", "data":"..."}
    """
    if not GOOGLE_API_KEY:
        error_msg = "GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)

    generated_images = []

    # Gemini 클라이언트 초기화
    try:
        print(f"[INFO] Gemini 클라이언트 초기화 중...")
        client = genai_client.Client(api_key=GOOGLE_API_KEY)
        print(f"[INFO] Gemini 클라이언트 초기화 완료")
    except Exception as e:
        error_msg = f"Gemini 클라이언트를 초기화할 수 없습니다: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise ValueError(error_msg)


    # 원본 이미지 로드 (시각적 참조용)
    print(f"[INFO] 원본 제품 이미지 로드: {image_path}")
    original_product_image = Image.open(image_path)
    print(f"[INFO] 원본 이미지 크기: {original_product_image.size}")
    for idx, prompt_data in enumerate(prompts):
        try:
            # 이미지 생성
            print(f"[INFO] 이미지 생성 중 ({idx+1}/{len(prompts)}): {prompt_data['title']}")
            print(f"[DEBUG] 프롬프트: {prompt_data['description'][:100]}...")

            # Gemini 2.5 Flash Image를 사용하여 이미지 생성
            print(f"[DEBUG] API 호출 중 - 모델: gemini-2.5-flash-image")
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[
                    "이 제품 이미지와 동일한 디자인을 유지하면서 다음 장면을 생성해주세요:",
                    original_product_image,
                    f"장면 설명: {prompt_data['description']}"
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="1:1")
                )
            )
            print(f"[DEBUG] API 응답 수신 완료")

            # 생성된 이미지 처리
            if response and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]

                # finish_reason 로깅
                finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
                print(f"[DEBUG] Finish reason: {finish_reason}")

                # Safety ratings 로깅
                if hasattr(candidate, 'safety_ratings') and candidate.safety_ratings:
                    print(f"[DEBUG] Safety ratings:")
                    for rating in candidate.safety_ratings:
                        print(f"  - {rating.category}: {rating.probability}")

                # content가 None인지 체크
                if not candidate.content:
                    error_msg = f"콘텐츠가 생성되지 않았습니다. Finish reason: {finish_reason}"
                    print(f"[WARNING] {error_msg}")

                    # Safety filter로 차단되었는지 확인
                    if 'SAFETY' in str(finish_reason):
                        error_msg = "안전 필터에 의해 차단되었습니다. 프롬프트를 수정해주세요."

                    image_info = {
                        "id": idx + 1,
                        "title": prompt_data["title"],
                        "prompt": prompt_data["description"],
                        "status": "error",
                        "message": error_msg
                    }
                    generated_images.append(image_info)
                    continue

                # 이미지 데이터 추출
                image_data = None
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            image_data = part.inline_data.data
                            break
                else:
                    print(f"[WARNING] Content에 parts가 없습니다.")

                if image_data:
                    # bytes를 base64로 인코딩
                    if isinstance(image_data, bytes):
                        # bytes인 경우 base64로 인코딩
                        base64_image = base64.b64encode(image_data).decode('utf-8')
                    else:
                        # 이미 base64 문자열인 경우
                        base64_image = image_data

                    # data URI 형식으로 변환
                    data_uri = f"data:image/png;base64,{base64_image}"

                    print(f"✓ 이미지 생성 완료 ({idx+1}/{len(prompts)})")

                    image_info = {
                        "id": idx + 1,
                        "title": prompt_data["title"],
                        "prompt": prompt_data["description"],
                        "status": "ok",
                        "type": "base64",
                        "data": data_uri
                    }
                    generated_images.append(image_info)
                else:
                    print(f"✗ 이미지 생성 실패: 응답에 이미지 데이터가 없습니다.")
                    image_info = {
                        "id": idx + 1,
                        "title": prompt_data["title"],
                        "prompt": prompt_data["description"],
                        "status": "error",
                        "message": "이미지 생성에 실패했습니다. (이미지 데이터 없음)"
                    }
                    generated_images.append(image_info)
            else:
                print(f"✗ 이미지 생성 실패: 응답이 없습니다.")
                image_info = {
                    "id": idx + 1,
                    "title": prompt_data["title"],
                    "prompt": prompt_data["description"],
                    "status": "error",
                    "message": "이미지 생성에 실패했습니다. (응답 없음)"
                }
                generated_images.append(image_info)

        except Exception as e:
            # 개별 이미지 생성 오류
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"[ERROR] 이미지 생성 오류 ({idx+1}/{len(prompts)})")
            print(f"[ERROR] 오류 유형: {error_type}")
            print(f"[ERROR] 오류 메시지: {error_msg}")
            import traceback
            traceback.print_exc()

            image_info = {
                "id": idx + 1,
                "title": prompt_data["title"],
                "prompt": prompt_data["description"],
                "status": "error",
                "message": f"{error_type}: {error_msg}"
            }
            generated_images.append(image_info)

    return generated_images


@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """이미지 업로드 및 분석"""
    if 'file' not in request.files:
        return jsonify({'error': '파일이 없습니다.'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400

    try:
        # 파일 저장
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 이미지 분석
        analysis = analyze_product_image(filepath)

        return jsonify({
            'success': True,
            'filename': filename,
            'analysis': analysis
        })

    except Exception as e:
        return jsonify({'error': f'오류 발생: {str(e)}'}), 500


@app.route('/generate', methods=['POST'])
def generate_images():
    """이미지 생성"""
    data = request.json
    filename = data.get('filename')
    num_images = min(int(data.get('num_images', 10)), 10)

    if not filename:
        error_msg = '파일명이 필요합니다.'
        print(f"[ERROR] {error_msg}")
        return jsonify({'error': error_msg}), 400

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"[INFO] 이미지 생성 시작 - 파일: {filename}, 개수: {num_images}")

        # 이미지 분석
        print(f"[INFO] 1단계: 이미지 분석 중...")
        analysis = analyze_product_image(filepath)
        print(f"[INFO] 이미지 분석 완료 - 제품: {analysis.get('product_name', 'Unknown')}")

        # 프롬프트 생성
        print(f"[INFO] 2단계: 프롬프트 생성 중...")
        prompts = generate_image_prompts(analysis, num_images)
        print(f"[INFO] 프롬프트 생성 완료 - {len(prompts)}개")

        # 이미지 생성
        print(f"[INFO] 3단계: AI 이미지 생성 중... (시간이 걸릴 수 있습니다)")
        generated = generate_images_with_gemini(analysis, prompts, filepath)
        success_count = sum(1 for img in generated if img.get('status') == 'ok')
        print(f"[INFO] 이미지 생성 완료 - 성공: {success_count}/{len(generated)}")

        return jsonify({
            'success': True,
            'analysis': analysis,
            'generated_images': generated
        })

    except ValueError as e:
        error_msg = f'설정 오류: {str(e)}'
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f'이미지 생성 중 오류 발생: {str(e)}'
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': error_msg,
            'error_type': type(e).__name__,
            'error_details': str(e)
        }), 500


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """업로드된 파일 제공"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/generated/<filename>')
def generated_file(filename):
    """생성된 파일 제공"""
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)


@app.route('/health')
def health():
    """헬스 체크"""
    return jsonify({
        'status': 'ok',
        'api_configured': bool(GOOGLE_API_KEY),
        'gemini_image_ready': bool(GOOGLE_API_KEY)
    })


if __name__ == '__main__':
    # Railway는 PORT 환경 변수를 제공하므로 이를 사용
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
