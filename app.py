"""
제품 이미지 생성 웹 애플리케이션
Google Gemini API를 활용하여 제품 이미지를 분석하고 관련 이미지를 생성합니다.
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
        raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")

    # Gemini Pro Vision 모델 사용
    model = genai.GenerativeModel('gemini-nano')

    # 이미지 로드
    img = Image.open(image_path)

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

    response = model.generate_content([prompt, img])

    # JSON 파싱
    try:
        # 응답에서 JSON 추출 (마크다운 코드 블록 제거)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        analysis = json.loads(response_text.strip())
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 기본값 반환
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
        raise ValueError("GOOGLE_API_KEY가 설정되지 않았습니다.")

    model = genai.GenerativeModel('gemini-nano')

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

    response = model.generate_content(prompt)

    try:
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        prompts_data = json.loads(response_text.strip())
        return prompts_data['prompts'][:num_images]
    except (json.JSONDecodeError, KeyError):
        # 기본 프롬프트 생성
        return [
            {"title": f"제품 사용 장면 {i+1}", "description": f"{analysis['product_name']}을(를) 사용하는 모습"}
            for i in range(num_images)
        ]


def generate_images_with_gemini(analysis, prompts):
    """
    Gemini API를 사용하여 이미지 생성 (시뮬레이션)
    참고: 현재 Gemini는 직접적인 이미지 생성을 제공하지 않으므로,
    실제로는 Imagen API나 다른 이미지 생성 API를 사용해야 합니다.
    """
    generated_images = []

    for idx, prompt_data in enumerate(prompts):
        # 실제 구현에서는 여기서 이미지 생성 API를 호출
        # 예: Stability AI, DALL-E, Midjourney API 등

        # 현재는 프롬프트 정보만 저장
        image_info = {
            "id": idx + 1,
            "title": prompt_data["title"],
            "prompt": prompt_data["description"],
            "filename": f"generated_{idx+1}.jpg",
            "status": "prompt_ready",  # 실제로는 "generated"가 됨
            "message": "이미지 생성을 위해서는 이미지 생성 API 키가 필요합니다."
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
        return jsonify({'error': '파일명이 필요합니다.'}), 400

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 이미지 분석
        analysis = analyze_product_image(filepath)

        # 프롬프트 생성
        prompts = generate_image_prompts(analysis, num_images)

        # 이미지 생성 (현재는 프롬프트만 반환)
        generated = generate_images_with_gemini(analysis, prompts)

        return jsonify({
            'success': True,
            'analysis': analysis,
            'generated_images': generated
        })

    except Exception as e:
        return jsonify({'error': f'오류 발생: {str(e)}'}), 500


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
        'api_configured': bool(GOOGLE_API_KEY)
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
