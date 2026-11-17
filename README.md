# 대한민국 하천 모니터

## 배포
GitHub 저장소에 파일을 올린 뒤 https://share.streamlit.io/ 에서 Repository, `main`, `app.py`를 선택해 배포합니다.

## 기상청 API 키
공공데이터포털의 [기상청 단기예보 조회서비스](https://www.data.go.kr/data/15084084/openapi.do)를 신청합니다. Streamlit Cloud의 App settings > Secrets에 다음을 입력합니다.

```toml
KMA_SERVICE_KEY = "발급받은_일반인증키"
```

앱은 초단기실황의 RN1(최근 1시간 강수량)을 조회합니다. 당일 누적 강수량이나 유역 평균 강수량과는 다릅니다.

## 전국 하천 지도 데이터
[기후에너지환경부 하천 공간정보](https://www.data.go.kr/data/15165046/fileData.do)에서 SHP 파일을 받아 QGIS 등으로 WGS84(EPSG:4326) GeoJSON으로 변환한 뒤 `data/rivers.geojson`에 넣으세요. GeoJSON 속성에 하천명이 있어야 합니다. 인식 속성명: `하천명`, `하천명칭`, `river_name`, `name`, `NAME`, `하천`.

## 수문·하상계수·범람확률
[한강홍수통제소 표준수문DB](https://www.data.go.kr/data/15083252/fileData.do)는 지점별 강수량·수위·유량·댐·보·홍수예보 자료를 안내합니다. [수위관측소 정보](https://www.data.go.kr/data/15117648/fileData.do)로 관측소와 하천을 연결할 수 있습니다.

하상계수는 모든 하천에 대해 자동 제공되는 값이라고 가정하지 않습니다. 공식 문서에서 확인한 값과 산정 기준을 별도 데이터로 관리해야 합니다. 실제 범람 확률(%)을 표시하려면 과거 강우·수위·유량·범람 기록, 하천 단면, 제방고, 계획홍수위 등을 모아 모델을 학습하고 독립 자료로 검증해야 합니다.

이 프로젝트는 교육·연구용 프로토타입이며 공식 홍수예보·재난안전 서비스가 아닙니다.
