import os, json, math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests, streamlit as st, folium
from streamlit_folium import st_folium

st.set_page_config(page_title='대한민국 하천 모니터', page_icon='🌊', layout='wide')
ROOT=os.path.dirname(os.path.abspath(__file__))
GEO=os.path.join(ROOT,'data','rivers.geojson')
KST=ZoneInfo('Asia/Seoul')
st.title('🌊 대한민국 하천 모니터')
st.caption('전국 하천 공간정보와 기상 관측을 연결하는 모니터링 프로토타입')
st.error('이 사이트는 공식 홍수 예보 시스템이 아닙니다. 현재 연결된 자료만으로 실제 범람 확률(%)을 계산할 수 없습니다. 대피·안전 판단에는 기상청·홍수통제소·지자체의 공식 안내를 확인하세요.')

@st.cache_data
def load_geo():
    if not os.path.exists(GEO): return {'type':'FeatureCollection','features':[]}
    with open(GEO,encoding='utf-8') as f: return json.load(f)

def river_name(f):
    p=f.get('properties') or {}
    for k in ('하천명','하천명칭','river_name','name','NAME','하천'):
        if p.get(k): return str(p[k])
    return '이름 미상 하천'

def center_of(g):
    pts=[]
    def walk(x):
        if isinstance(x,list):
            if len(x)>=2 and isinstance(x[0],(int,float)) and isinstance(x[1],(int,float)): pts.append((x[1],x[0]))
            else:
                for v in x: walk(v)
    walk(g.get('coordinates',[]))
    if not pts: return None
    return (sum(p[0] for p in pts)/len(pts),sum(p[1] for p in pts)/len(pts))

def secret(k):
    try: return st.secrets.get(k,os.getenv(k,''))
    except Exception: return os.getenv(k,'')

def grid_xy(lat,lon):
    # 기상청 Lambert Conformal Conic 격자 변환
    re=6371.00877/5.0; d=math.pi/180; sl1=30*d; sl2=60*d; olon=126*d; olat=38*d; xo=43; yo=136
    sn=math.log(math.cos(sl1)/math.cos(sl2))/math.log(math.tan(math.pi/4+sl2/2)/math.tan(math.pi/4+sl1/2))
    sf=math.tan(math.pi/4+sl1/2)**sn*math.cos(sl1)/sn
    ro=re*sf/(math.tan(math.pi/4+olat/2)**sn)
    ra=re*sf/(math.tan(math.pi/4+lat*d/2)**sn)
    th=lon*d-olon
    if th>math.pi: th-=2*math.pi
    if th<-math.pi: th+=2*math.pi
    th*=sn
    return int(ra*math.sin(th)+xo+0.5),int(ro-ra*math.cos(th)+yo+0.5)

def kma_rn1(lat,lon,key):
    now=datetime.now(KST)-timedelta(minutes=40)
    now=now.replace(minute=(now.minute//10)*10,second=0,microsecond=0)
    nx,ny=grid_xy(lat,lon)
    url='https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
    params={'serviceKey':key,'pageNo':1,'numOfRows':100,'dataType':'JSON','base_date':now.strftime('%Y%m%d'),'base_time':now.strftime('%H%M'),'nx':nx,'ny':ny}
    res=requests.get(url,params=params,timeout=20); res.raise_for_status(); data=res.json().get('response',{})
    head=data.get('header',{})
    if head.get('resultCode') not in (None,'00'): raise RuntimeError(head.get('resultMsg','기상청 응답 오류'))
    items=data.get('body',{}).get('items',{}).get('item',[])
    for x in items:
        if x.get('category')=='RN1':
            v=str(x.get('obsrValue','')).strip()
            try: return (0.0 if v in ('강수없음','-','') else float(v)),now.strftime('%Y-%m-%d %H:%M')
            except ValueError: return None,now.strftime('%Y-%m-%d %H:%M')
    return None,now.strftime('%Y-%m-%d %H:%M')

geo=load_geo(); features=geo.get('features',[])
if not features: st.warning('전국 하천 선형 자료가 아직 없습니다. 공식 SHP 자료를 GeoJSON으로 변환해 data/rivers.geojson에 넣어야 하천 검색과 지도 표시가 작동합니다.')
q=st.text_input('하천 이름 검색',placeholder='예: 한강, 낙동강, 금강')
matched=[f for f in features if q.strip() and q.strip() in river_name(f)]
if q.strip() and not matched: st.info('등록된 공간자료에서 하천 이름을 찾지 못했습니다.')
sel=matched[0] if matched else None
center=center_of(sel['geometry']) if sel else (36.4,127.8)
m=folium.Map(location=center,zoom_start=11 if sel else 7,tiles='OpenStreetMap',control_scale=True)
for f in features:
    chosen=bool(sel and f is sel)
    folium.GeoJson(f,style_function=lambda feat,c=chosen:{'color':'#2563eb' if c else '#64748b','weight':5 if c else 2,'opacity':0.9},tooltip=river_name(f)).add_to(m)
st_folium(m,use_container_width=True,height=620,returned_objects=[])

key=secret('KMA_SERVICE_KEY')
if sel:
    st.subheader('선택 하천: '+river_name(sel))
    pt=center_of(sel['geometry'])
    if key and pt:
        try:
            rain,stamp=kma_rn1(pt[0],pt[1],key)
            a,b,c=st.columns(3)
            a.metric('최근 1시간 강수량','자료 없음' if rain is None else f'{rain:g} mm')
            b.metric('위도',f'{pt[0]:.4f}'); c.metric('경도',f'{pt[1]:.4f}')
            st.caption(f'기상청 초단기실황 기준시각: {stamp} KST · RN1은 최근 1시간 강수량이며 당일 누적 강수량이 아닙니다.')
        except Exception as e: st.error(f'기상청 자료 조회 실패: {e}')
    elif not key: st.info('실시간 강수량 조회를 위해 기상청 API 인증키를 Streamlit Secrets에 등록하세요.')

st.subheader('실제 범람 확률을 계산하려면')
st.write('하천별 수위·유량 관측소 연결, 경보 기준·계획홍수위, 하천 단면·제방 정보, 유역 강우, 과거 범람 기록이 필요합니다. 하상계수 하나만으로는 범람 확률을 구할 수 없습니다. 검증된 모델이 준비되기 전에는 임의의 퍼센트를 표시하지 않습니다.')
st.caption('현재 지도는 하천 위치와 검색을 표시합니다. 파란색은 검색된 하천 강조 표시이며 위험 단계 색상이 아닙니다.')
