"""bias_check.py
================
바이어스 노드가 살아 있는지 본다. 단극(GND 기준)으로 절대 전압을 읽는다.

**왜 따로 필요한가**
평소 측정은 차동(A0-A1)이다. 그런데 1단계처럼 두 입력을 같은 노드에 단락시켜
두면 차동은 무엇이 잘못돼 있어도 0 이 나온다. 실제로 바이어스 분압에 저항 대신
커패시터가 꽂혀 노드가 떠 있었는데도 차동은 0.219 mV 로 조용했다(CLAUDE.md 0절 ⑩).
공통 성분이 전부 상쇄됐기 때문이다. 그래서 절대 전압을 따로 봐야 한다.

합격 기준 — A0·A1 이 **1.65 V(3.3 V 의 절반) 근처**이고, 20초 동안 흔들림이
수 mV 안에 머문다. 저항 분압이면 그렇게 나온다. 떠 있으면 엉뚱한 값에서
수백 mV 폭으로 방황한다.

**전극을 식물에 꽂은 뒤에는** A0·A1 = 1.65 V + 각 전극 전압(반쪽전지 전위)이라 수백 mV 벗어나는 게 정상이다.
그때는 **A2 를 분압 중점(흙 기준선이 꽂힌 줄)에 점퍼로 이어** 기준 전압을 직접 본다(2026-10-21, CLAUDE.md ㉞).
A2 가 1.65 V 근처로 조용하면 기준 전압은 정상이다.

⚠️ 대시보드(main.py --web)가 같은 ADS1115 를 읽는 중에 돌리면, 이 스크립트의 단발 읽기가 칩 설정(채널·이득·모드)을
바꿔 실시간 화면이 엉뚱한 값을 보일 수 있다(⑯). 수집은 시작할 때 칩을 다시 맞추므로 기록은 괜찮다.
점검 뒤에는 대시보드를 재시작한다(sudo systemctl restart plant-dashboard).

    venv/bin/python3 src/bias_check.py
"""
import os
import time

import board, busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

VDD = 3.3
EXPECT = VDD / 2            # 분압이 살아 있을 때 폴로어 출력
SETTLE_TOL_V = 0.010        # 20초 흔들림이 이 안이면 "눌려 있다"고 본다
NEAR_TOL_V = 0.10           # 기대값에서 이만큼 안이면 합격


def dashboard_running():
    """대시보드(같은 칩을 읽는 프로세스)가 떠 있는가. /proc 의 명령줄을 본다."""
    me = os.getpid()
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) == me:
            continue
        try:
            with open(f"/proc/{d}/cmdline", "rb") as f:
                cmd = f.read().replace(b"\0", b" ").decode("utf-8", "ignore")
        except OSError:
            continue
        if "web_dashboard" in cmd or ("main.py" in cmd and "--web" in cmd):
            return True
    return False


def judge(reads, spans, swing):
    """판정 문장들을 돌려준다. reads = A0~A3 평균(V), spans = 각 채널 8번 읽기의 폭(V), swing = A0 20초 흔들림 폭(V).
    A2 가 분압 중점에 이어져 있으면(1.65 V 근처·조용) 그것으로 기준 전압을 판정한다."""
    out = []
    # 떠 있는 채널은 0.6 V 근처에서 100 mV 넘게 방황한다(⑪). 이어져 있으면 수 mV 안이다.
    a2_ref = abs(reads[2] - EXPECT) < NEAR_TOL_V / 2 and spans[2] < 2 * SETTLE_TOL_V
    near = abs(reads[0] - EXPECT) < NEAR_TOL_V and abs(reads[1] - EXPECT) < NEAR_TOL_V
    steady = swing < SETTLE_TOL_V
    if a2_ref:
        out.append(f"기준 전압 정상 — A2(분압 중점) {reads[2]:.4f} V, 흔들림 {spans[2] * 1000:.1f} mV.")
        if not near:
            out.append(f"A0·A1 이 1.65 V 에서 {(reads[0] - EXPECT) * 1000:+.0f} / {(reads[1] - EXPECT) * 1000:+.0f} mV 벗어났다 — "
                       "전극을 꽂은 상태라면 전극 전압 때문이라 정상이다. 전극이 없는데 이러면 폴로어 배선을 보라.")
        if not steady:
            out.append(f"A0 흔들림 {swing * 1000:.0f} mV — 기준 전압은 조용하므로 전극·식물 쪽으로 들어오는 잡음이다"
                       "(상자 밖이면 상용전원 성분이 흔하다).")
        return out
    if near and steady:
        return ["합격 — 바이어스 분압이 살아 있다."]
    if not near:
        return [f"불합격 — A0/A1 이 {EXPECT:.2f} V 에서 너무 멀다. 전극이 없다면 분압에 저항이 아니라 커패시터가 꽂혀 있는지 보라(CLAUDE.md ⑩).",
                "전극을 식물에 꽂은 상태라면 전극 전압만큼 벗어나는 게 정상이다 — A2 를 분압 중점에 이어 다시 재 보라."]
    return ["불합격 — 값은 맞지만 너무 흔들린다. 접촉과 배선을 보라."]


def _pins():
    """라이브러리 버전에 따라 ADS.P0 이 없다. frontend.py 와 같은 방식으로 푼다."""
    return [getattr(ADS, f"P{i}", i) for i in range(4)]


def main():
    busy = dashboard_running()
    if busy:
        print("⚠️ 대시보드가 같은 ADS1115 를 읽는 중이다. 이 점검 뒤 실시간 화면이 엉뚱한 값을 보일 수 있으니"
              " 끝나면 재시작하라(sudo systemctl restart plant-dashboard).\n")
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    ads.gain = 1            # ±4.096 V — 3.3 V 계를 다 담는다
    P = _pins()

    labels = ["A0 (폴로어 A 출력)", "A1 (폴로어 B 출력)", "A2", "A3"]
    print(f"기대값: 분압이 살아 있으면 A0/A1 이 {EXPECT:.2f} V 근처\n")

    reads, spans = [], []
    for p, label in zip(P, labels):
        ch = AnalogIn(ads, p)
        vs = [ch.voltage for _ in range(8)]
        avg = sum(vs) / len(vs)
        reads.append(avg)
        spans.append(max(vs) - min(vs))
        print(f"{label:22s} {avg:7.4f} V   (min {min(vs):.4f} / max {max(vs):.4f})")

    print(f"\nA0 을 20초 추적 (떠 있으면 한 방향으로 흐르거나 크게 방황한다)")
    ch = AnalogIn(ads, P[0])
    t0 = time.time()
    track = []
    while time.time() - t0 < 20:
        v = ch.voltage
        track.append(v)
        print(f"  {time.time() - t0:5.1f}s  {v:7.4f} V")
        time.sleep(2)

    swing = max(track) - min(track)
    print(f"\n20초 흔들림 폭: {swing * 1000:.1f} mV")
    for line in judge(reads, spans, swing):
        print(line)
    if busy:
        print("\n⚠️ 대시보드를 재시작하라: sudo systemctl restart plant-dashboard")


if __name__ == "__main__":
    main()
