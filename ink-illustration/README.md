# 송림의 숨결 — 전통 수묵 일러스트 모션 그래픽

정교한 호랑이의 털과 수염, 소나무 솔잎, 산수의 담묵과 한지 질감을 살린 **일러스트 기반 모션 그래픽**입니다.

- 15초 · 9:16 · 1080×1920 · 24fps · 360프레임
- H.264 MP4 · 무음 · 자막/로고/워터마크 없음
- 먹 번짐으로 원화가 드러나고, 산 사이의 안개와 솔가지·수면·단풍잎이 잔잔하게 움직입니다.
- 얼굴의 정교한 붓선은 유지하고 주변 풍경에 절제된 움직임을 적용합니다.

[영상 다운로드](https://raw.githubusercontent.com/aa66161533-blip/motion-graphicsCapCut-motion-graphics-and-video-projects/main/ink-illustration/renders/traditional_ink_15s.mp4)

갤럭시 탭에서는 링크를 길게 눌러 **링크 다운로드**를 선택하세요. **내 파일 → 다운로드**에서 확인할 수 있습니다.

## 재현

Python 3.10 이상과 FFmpeg/FFprobe가 필요합니다.

```bash
python -m pip install -r requirements.txt
python render.py
```

`assets/painting.png`와 `assets/leaf.png`는 이 프로젝트를 위해 이미지 생성 도구로 제작한 원화입니다. Python은 먹 번짐, 부분 메시 변형, 잔잔한 수면, 반투명 안개, 작은 단풍잎의 이동을 합성하며 FFmpeg로 MP4를 인코딩합니다.

완성 파일은 `renders/traditional_ink_15s.mp4`, 검증 결과는 `renders/verification.json`입니다. 영상 길이·해상도·프레임 수·오디오 트랙 유무와 전체 디코딩을 검사합니다.
