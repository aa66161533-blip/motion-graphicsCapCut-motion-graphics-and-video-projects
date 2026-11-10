# Today I Cheer for You — 원본 보존 커피 모션 그래픽

현재 상태: 원본 이미지 파일 입력 대기. 완성 MP4가 아직 생성되지 않았습니다.

원본 영문을 이미지 픽셀로 보존하며 재생성하거나 다시 타이핑하지 않습니다. 원본의 색감과 구도를 유지하는 패럴랙스 합성 방식이며, 실제 3D 모델을 사용하는 방식은 아닙니다.

- 0~3초: 원본 제목을 첫 프레임부터 유지하며 부드럽게 확대
- 3~6초: 커피잔 위로 올라가는 따뜻한 김
- 6~10초: 상단 단풍잎의 바람 움직임
- 10~13초: 원본 황금빛 하트의 빛과 반짝임
- 13~15초: 원래 구도로 천천히 축소
- 출력: 1080×1920, 30fps, 정확히 450프레임, 무음 H.264 MP4

## 실행

Python 3.11 이상과 FFmpeg/FFprobe가 필요합니다.

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python render.py --image /path/to/coffee-original.png --output renders/output.mp4
```

입력은 첨부한 원본 PNG/JPG 파일을 사용하세요. 기본 입력 위치는 `assets/coffee-original.png`입니다. JPG 입력도 `--image`로 지정할 수 있습니다.

중간 화면만 확인:

```sh
python render.py --image /path/to/coffee-original.png --preview
```

렌더링 후 프레임 수·길이·코덱·해상도·프레임레이트·무음·전체 디코딩을 검사하고 `renders/verification.json`에 기록합니다. 원본 글자는 다시 생성하지 않지만, 최종 글자 가독성은 원본 파일로 렌더링한 후 시각 확인해야 합니다.
