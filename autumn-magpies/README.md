# 추경 — 흐르는 물과 까치의 대화

제공된 가을 수묵담채화를 바탕으로 제작한 연속 15초 영상입니다. 1080×1920, 24fps, H.264 MP4, 무음입니다. 지저귀는 모습은 부리, 목, 고개의 움직임으로 표현합니다.

폭포의 하강 흐름, 계류의 파문, 이동하는 옅은 물안개, 단풍의 미세한 흔들림과 까치 두 마리의 독립적인 움직임을 합성합니다. 실사 영상이 아닌 원화의 붓 터치를 유지하는 애니메이션입니다. 원화는 첨부 이미지를 참고하여 애니메이션용으로 재구성한 이미지입니다.

## 실행

Python 3.11 이상과 FFmpeg가 필요합니다.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python render.py
```

`renders/autumn_magpies_15s.mp4`와 전체 디코딩·규격 검사 결과 `renders/verification.json`을 생성합니다.

## 다운로드

[MP4 영상 다운로드](https://raw.githubusercontent.com/aa66161533-blip/motion-graphicsCapCut-motion-graphics-and-video-projects/main/autumn-magpies/renders/autumn_magpies_15s.mp4)

갤럭시 탭에서 링크를 길게 누른 뒤 **링크 다운로드**를 선택하면 내 파일 → 다운로드에서 볼 수 있습니다.
