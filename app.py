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
