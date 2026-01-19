# Reynolds-Cal-01 (MS Teams Workflow 예제)

이 가이드는 **MS Teams 워크플로우**와 **GitHub Actions**를 연동하여 유체역학의 핵심 지표인 레이놀즈 수($Re$)를 자동 계산하는 시스템을 처음부터 끝까지 구축하는 상세 매뉴얼입니다.

---

## 🏁 프로젝트 준비물

1. **GitHub 저장소:** 파이썬 코드가 저장될 레포지토리.
    
2. **MS Teams:** 워크플로우 앱 및 결과를 받을 채널.
    
3. **Obsidian:** 설정 과정과 기술 노트를 기록할 도구.
    

---

## 1단계: GitHub 저장소 설정 (연산부 구축)

먼저 GitHub 저장소에 계산을 수행할 엔진과 외부 신호를 받을 통로를 만듭니다.

### ① 파이썬 스크립트 작성 (app.py)

저장소 루트(Root) 위치에 아래 파일을 생성합니다. Teams에서 보낸 JSON 데이터를 해석하여 계산하는 로직이 포함되어 있습니다.

Python

```
import os
import json

def calculate_reynolds(v, l):
    # 공기의 물리적 상수 (20°C 기준)
    rho = 1.225  # 밀도 [kg/m^3]
    mu = 1.789e-5 # 점성 계수 [kg/m·s]
    return (rho * v * l) / mu

def main():
    # 1. Teams 워크플로우가 보낸 페이로드 데이터 수신
    payload_raw = os.getenv("INPUT_DATA")
    
    try:
        payload = json.loads(payload_raw) if payload_raw else {}
        # 문자열로 들어오는 입력을 숫자(float)로 변환
        v = float(payload.get("velocity", 10.0))
        l = float(payload.get("length", 0.1))
        
        # 2. 레이놀즈 수 계산
        re = calculate_reynolds(v, l)
        
        print(f"--- CFD 계산 보고서 ---")
        print(f"입력 유속 (v): {v} m/s")
        print(f"특성 길이 (L): {l} m")
        print(f"계산된 레이놀즈 수 (Re): {re:.2f}")

        # 3. 결과를 다음 단계(Teams 알림)에서 쓸 수 있도록 기록
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"re_result={re:.2f}\n")
                
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    main()
```

### ② GitHub Actions 워크플로우 작성 (.github/workflows/main.yml)

Teams에서 '디스패치(Dispatch)' 신호를 보냈을 때 위 스크립트를 실행하는 자동화 명세서입니다.

YAML

```
name: Reynolds Number Calculator

on:
  repository_dispatch:
    types: [reynolds-calc] # Teams의 이벤트 이름과 반드시 일치해야 함

jobs:
  compute:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Run Calculation
        id: py_run
        env:
          INPUT_DATA: ${{ toJson(github.event.client_payload) }}
        run: python app.py

      - name: Notify Teams
        if: success()
        run: |
          curl -H "Content-Type: application/json" \
          -d '{
                "text": "✅ **계산 완료**\n\n- **유속:** ${{ github.event.client_payload.velocity }} m/s\n- **길이:** ${{ github.event.client_payload.length }} m\n- **결과 (Re):** ${{ steps.py_run.outputs.re_result }}"
              }' \
          ${{ secrets.TEAMS_WEBHOOK_URL }}
```

---

## 2단계: MS Teams 워크플로우 설정 (사용자 인터페이스)

이제 Teams에서 값을 입력받는 창을 만듭니다.


### ① 트리거: '키워드가 맨션될 때' 단계 추가
워크플로우 앱에서 **'키워드가 맨션될 때'** 작업을 추가하고 [메시지 유형] 칸은 **'채널'**, [검색할 키워드] 칸은 '**/run-reynum'**, 입력하고 그 외 팀과 채널은 적절하게 선택하고 이어서 **"새 단계"**를 추가합니다.

### ② 동작: 적응형 카드 단계 추가

워크플로우 앱에서 **'적응형 카드를 게시 및 응답 대기'** 작업을 추가하고 [다음으로 게시] 칸에는 **'흐름 봇'**, [게시 위치] 칸은 **'채널'** [메시지] 칸에 아래 JSON을 붙여넣습니다. 데이터 타입 충돌을 방지하기 위해 `Input.Text`를 사용했습니다. 


JSON

```
{
    "type": "AdaptiveCard",
    "body": [
        { "type": "TextBlock", "text": "📊 레이놀즈 수 계산기", "weight": "Bolder", "size": "Medium" },
        { "type": "Input.Text", "id": "v_input", "label": "유체 속도 (m/s)", "style": "decimal" },
        { "type": "Input.Text", "id": "l_input", "label": "특성 길이 (m)", "style": "decimal" }
    ],
    "actions": [{ "type": "Action.Submit", "title": "GitHub 전송" }],
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "version": "1.4"
}
```

### ③ 동작: GitHub 연결 단계 추가

**Github** 앱을 선택하고 **'리포지토리 디스패치 이벤트 만들기'** 작업을 추가하고 아래와 같이 설정합니다.

- **리포지토리 소유자/이름:** 본인의 정보 입력. (Github의 리포지토리 소유자 및 이름 입력)
    
- **이벤트 이름:** `reynolds-calc` (적절한 이름 입력)
    
- **이벤트 페이로드:**
    
    JSON
    
    ```
    {
      "velocity": "@{outputs('적응형_카드_게시_및_응답_대기')?['body/data/v_input']}",
      "length": "@{outputs('적응형_카드_게시_및_응답_대기')?['body/data/l_input']}"
    }
    ```
    

---

## 3단계: 보안 및 최종 점검

### ① Webhook URL 등록

1. 해당 Teams 채널의 '채널 관리'에서 **'Incoming Webhook'** 커넥터를 생성하고 URL을 복사합니다.
	- Name 입력 후 'Create' 를 클릭하면 URL이 생성됩니다.
    
2. GitHub 저장소의 **Settings > Secrets and variables > Actions**에서 `TEAMS_WEBHOOK_URL_Exam`이라는 이름으로 해당 URL을 저장합니다.
    

### ② 실행 및 수식 확인

모든 설정이 완료되면 Teams에서 워크플로우를 실행하여 값을 입력합니다. GitHub Actions가 정상 작동하면 아래 수식에 기반한 결과가 채널로 돌아옵니다.

$$Re = \frac{\rho v L}{\mu}$$
