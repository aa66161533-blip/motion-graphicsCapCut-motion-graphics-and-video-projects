# 황금빛 가을의 숨결

첨부된 단풍 산경 사진의 구도와 색감을 참고해 재구성한 원화를 사용한 15초 모션 그래픽입니다. 세로 9:16, 1080×1920, 24fps, 360프레임, H.264 MP4, 무음입니다.

단풍의 미세한 바람 움직임, 깊이에 따른 느린 카메라 전진, 이동하는 계곡 안개, 호수 반짝임, 작은 낙엽을 더했습니다. 자막과 로고는 없습니다.

## 실행

Python 3.11 이상, FFmpeg가 필요합니다.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python render.py
```

`renders/golden_autumn_15s.mp4`와 `renders/verification.json`을 생성합니다. 프레임 수, 재생 시간, 해상도, 코덱, 무음 및 전체 디코딩을 검증합니다.

[영상 다운로드](https://raw.githubusercontent.com/aa66161533-blip/motion-graphicsCapCut-motion-graphics-and-video-projects/main/golden-autumn/renders/golden_autumn_15s.mp4)

갤럭시 탭에서는 링크를 길게 눌러 **링크 다운로드** → 내 파일 → 다운로드에서 저장된 영상을 확인하세요.
