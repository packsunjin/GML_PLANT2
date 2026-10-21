"""상자 안 온도·습도(DHT11) 기록 — 2026-10-21, 패러데이 상자 본 실험(CLAUDE.md ㉝·㉞).

DHT11 은 리눅스 커널 드라이버로 읽는다(파이 5 에서는 파이썬 DHT 라이브러리가 안 되거나 불안정하다).
파이에서 한 번만: /boot/firmware/config.txt 에  dtoverlay=dht11,gpiopin=4  를 넣고 재부팅.
그러면 /sys/bus/iio/devices/iio:deviceN/ (name 파일이 dht11) 에서 값이 읽힌다.

배선: + → 17번 핀(3.3 V, 1번은 ADS1115 가 씀), out → 7번(GPIO4), − → 9번(GND).

DHT11 은 읽기가 자주 실패한다(EIO·타임아웃). 2초 간격으로 몇 번 다시 읽고, 그래도 안 되면 그 줄은 빈칸으로 둔다.
값은 정수 단위(온도 1 °C, 습도 1 %)이고 정확도는 대략 ±2 °C, ±5 % 다.
"""
import csv
import glob
import os
import threading
import time

IIO_ROOT = "/sys/bus/iio/devices"
ENV_SUFFIX = ".env.csv"


def env_path(csv_path):
    """전위 CSV 옆에 놓이는 온습도 파일 경로. 정상_3.csv → 정상_3.env.csv"""
    return os.path.splitext(csv_path)[0] + ENV_SUFFIX


def find_device(root=IIO_ROOT):
    """커널이 만든 DHT11 장치 폴더. 없으면 None(config.txt 설정 전이거나 센서 없음)."""
    for d in sorted(glob.glob(os.path.join(root, "iio:device*"))):
        try:
            with open(os.path.join(d, "name")) as f:
                if f.read().strip().startswith("dht11"):
                    return d
        except OSError:
            pass
    return None


def _read_milli(path):
    with open(path) as f:
        return int(f.read().strip()) / 1000.0


def read(dev, tries=3, gap=2.0):
    """(온도 °C, 습도 %) 를 돌려준다. tries 번 다 실패하면 None."""
    for k in range(tries):
        try:
            t = _read_milli(os.path.join(dev, "in_temp_input"))
            h = _read_milli(os.path.join(dev, "in_humidityrelative_input"))
            return t, h
        except (OSError, ValueError):
            if k < tries - 1:
                time.sleep(gap)
    return None


class EnvLogger:
    """수집하는 동안 period 초마다 온습도를 전위 CSV 와 **같은 시각축**(time.time() - start)으로 적는다.

    ⚠️ DHT11 은 읽을 때마다 데이터선이 몇 ms 동안 오르내린다. 선이 전극선 가까이 있으면 전위 기록에
    period 초 주기의 작은 튐이 생길 수 있다. 읽은 시각이 이 파일에 그대로 남으니 의심되면 맞춰 본다
    (1단계의 121초 주기 튐과는 다른 것이다).
    """

    def __init__(self, csv_path, start, period=60.0, dev=None):
        self.path = env_path(csv_path)
        self.start = start
        self.period = period
        self.dev = dev if dev is not None else find_device()
        self.rows = 0
        self.fails = 0
        self._stop = threading.Event()
        self._thread = None

    def begin(self):
        if self.dev is None:
            print("[env] 온습도 센서(DHT11)를 못 찾아 온습도는 기록하지 않습니다. "
                  "(config.txt 에 dtoverlay=dht11,gpiopin=4 를 넣고 재부팅했는지 확인)")
            return False
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["timestamp_sec", "temp_c", "humidity_pct"])
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[env] 온습도 {self.period:g}초마다 기록 -> {self.path}")
        return True

    def _run(self):
        next_t = 0.0
        while not self._stop.is_set():
            now = time.time() - self.start
            if now >= next_t:
                val = read(self.dev)
                t_rec = round(time.time() - self.start, 3)
                with open(self.path, "a", newline="", encoding="utf-8") as f:
                    if val is None:
                        self.fails += 1
                        csv.writer(f).writerow([t_rec, "", ""])
                    else:
                        csv.writer(f).writerow([t_rec, f"{val[0]:.1f}", f"{val[1]:.1f}"])
                self.rows += 1
                next_t += self.period
            self._stop.wait(min(1.0, max(0.05, next_t - (time.time() - self.start))))

    def end(self):
        if self._thread is None:
            return None
        self._stop.set()
        self._thread.join(timeout=10)
        print(f"[env] 온습도 {self.rows}줄 기록(읽기 실패 {self.fails}줄)")
        return {"env_file": os.path.basename(self.path), "env_rows": self.rows, "env_fails": self.fails}


if __name__ == "__main__":
    # 센서 점검: python3 env_sensor.py
    d = find_device()
    if d is None:
        print("DHT11 장치가 없습니다. config.txt 에 dtoverlay=dht11,gpiopin=4 를 넣고 재부팅하세요.")
    else:
        v = read(d)
        print(f"{d}: " + ("읽기 실패(배선 확인)" if v is None else f"온도 {v[0]:.1f} °C, 습도 {v[1]:.1f} %"))
