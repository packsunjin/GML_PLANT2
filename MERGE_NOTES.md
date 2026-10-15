# 병합 메모 (2026-10-14)

## 무엇을 합쳤나
기준 = `GML_PLANT-claude-dc-frontend`(2026-10-12) + 이전 대화에서 만든 수정(접촉/비접촉 화면·학습 탭·`report/g_analysis_2s.py`).
그 위에 **Drive `GML_PLANT` 폴더**(2026-10-13)의 바뀐 파일을 덮고, 마지막으로 **`files.zip`** 5개(가장 최신)를 덮었다.

| 출처 | 파일 |
|---|---|
| Drive | `main.py`, `src/{feature_extraction,preprocess,inference,sanity_check,spectro_render,gui,sensor_control,train}.py`, `src/band_filter.py`(새 파일), `models/best_model.joblib` |
| files.zip (최신) | `src/{frontend,live_spectrogram,web_dashboard}.py`, `src/live_spectrogram.html`, `src/live_admin.py`(새 파일) |
| 이전 대화 수정 | `web/live.html`, `web/static/live.js`, `web/chorokmal.html`(비접촉/접촉 표시, 학습 탭 접촉 전용) |

`src/web_dashboard.py`는 files.zip 것을 그대로 썼다. Drive 것에 이전 대화 수정이 이미 들어 있었고, files.zip은 그 위에 "판정 없음일 때도 신호를 흘려 보내는" 변경만 더한 것이라 충돌이 없었다.

## 빠진 것 / 주의
- `data/admin.json`(관리자 비밀번호·세션 키)은 Drive에 있던 것을 그대로 넣었다. `.gitignore`에 들어 있으니 GitHub에는 올리지 말 것.
- Drive 압축에는 `CLAUDE.md`, `web/`, `data/touch*` 등이 없었다(일부만 내려받은 듯). `CLAUDE.md`는 **2026-10-12 원본 그대로**라 ㉑㉒ 같은 이후 기록이 없다. 파이의 최신 `CLAUDE.md`를 덮어쓰지 말 것.
- 병합된 코드의 창·대역은 **30초 창 / 5초 이동 / 앞 문맥 90초 / 0.01–1Hz**다. 이전 대화에서 말한 2초 창은 이 코드에서 이미 바뀌어 있다.
- **옛 필터(0.5–20Hz)로 학습한 모델은 판정하지 않는다**(`inference.py`가 막음). `models/touch2s_ns`와 병합된 `models/best_model.joblib`도 확인 결과 이 경우였다. 새 필터로 수집→변환→학습해야 한다.
- `data/touch2s/` 폴더 이름에 "2s"가 남아 있지만 지금 창은 30초다. 이름만 낡았다.
- `report/g_analysis_2s.py`는 2초 창 기준 스크립트다. 창이 30초로 바뀌었으니 그대로 돌리면 현재 모델과 다른 조건이 된다.

## 2026-10-14 추가: 일반 페이지의 전위·스펙트로그램을 live 것으로 교체
- `web/chorokmal.html`: 옛 전위 캔버스·스펙트로그램 캔버스를 빼고 `/live?embed=1` iframe 으로 교체.
- `web/live.html`: `?embed=1` 모드 추가(게이지·제목·버튼 숨김, 두 그래프만, 높이를 부모에 알림).
- 이유: 옛 일반 페이지는 판정용 창 스펙트로그램(`d.spec`)을 그리는데, 판정 없음(문맥+창 120초 미만, 옛 필터 모델)에서는
  이 배열이 비어 그림이 그대로 멈춘다. live 쪽은 판정과 무관한 `live_spec` 열을 쓴다.
- 수집 중에는 수집 프로세스가 센서를 쓰므로(`pause_live`) live 그래프도 일부러 멈추고 머리줄에 일시정지가 뜬다.
