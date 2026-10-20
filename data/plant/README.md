# data/plant — 식물 측정 기록

보고서에 쓴 3단계 원본 `live_20260915_070020.csv` 는 여기 있다(2026-10-20, GML_PLANT2 에는 릴리스가 없어 git 본문에 넣음). 무효 기록(`*_INVALID*`, `tap_session*`)의 CSV 는 옛 저장소 packsunjin/GML_PLANT 릴리스 `data-2026-10` 에만 있다.

| 파일 | 내용 | 쓸 수 있나 |
|---|---|---|
| `live_20260915_070020.csv` | 실시간 스펙트로그램 페이지(`src/live_spectrogram.py`) 기록. 250 S/s, 약 2시간 (1,864,000 표본). 열: 표본 번호, 전압(mV) | **유효** — 보고서 Ⅳ-5~7 |
| `live_…marks.csv` | "쳤어" 버튼 시각(표본 번호) | 유효 |
| `*_INVALID_mux_A3.*` | 식물 3시간 기록 | **무효** — 라이브러리 채널 오류(CLAUDE.md 0절 ⑯), `README_INVALID.txt` |
| `tap_session_INVALID_two_writers.*` | 치기 기록 | **무효** — 기록 프로그램 두 개가 같은 파일에 씀(0절 ⑰) |
| `stim_log.txt` | 자극 시각 메모(PC 시각) | 참고 |

⚠️ **파일 이름의 날짜(2026-09-15)는 라즈베리파이 시계가 틀려서 생긴 것이다.** 실제 측정일은
2026-10-07 이다. `clock_offset.txt`: PC 시각 18:21:32 일 때 파이 시각 06:22:54.
