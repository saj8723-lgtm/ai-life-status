// Vercel Edge Function — パーソナライズOGP画像生成 (1200x630)
export const config = { runtime: 'edge' };
import { ImageResponse } from '@vercel/og';

const JOBS=["伝説の社畜","深夜のコンビニ賢者","布団の守護神","カフェイン魔術師","散財の錬金術師","孤高のソロキャンパー","妄想の建築家","通知の奴隷","AI魔法剣士","深夜ラーメン背徳者","ドライブの哲学者","推し活の聖女","副業沼の冒険者","永遠の計画マン","カフェ巡りの魔女","ストーリーズの女神","コスメ錬金術師","積ん読の大賢者","昼寝の大魔王","サブスク放置の貴族","推しの騎士","深夜アニメの求道者","Google検索の勇者","タピオカの巫女","Zoom疲れの勇者","TikTok沼の住人","推し活破産者","深夜Xの亡者","週末シェフ見習い","寝落ち配信の伴走者","ガジェット沼の住人","名言コレクターの賢者","筋トレ伝道師","サウナ道の求道者","ポイ活の大魔導士","終電ダッシュの勇者","有給消化の忍者","スタバ常駐の文豪","キャンプ装備コレクター","朝活宣言の戦士","自炊失敗の料理見習い","写真フォルダ整理師","ミーティング生存者","一気見配信の探偵","ガチャ沼の錬金術師","深夜筋トレの修行僧","週末旅人の吟遊詩人","ポッドキャスト中毒者","締め切り破壊神","Notion設計師","朝ラン失踪者","リール収集の魔術師"];
const JOBC=["#e84393","#7c5ce7","#fd79a8","#0984e3","#f9a825","#00b894","#7c5ce7","#fd79a8","#0984e3","#e84393","#7c5ce7","#fd79a8","#f9a825","#00b894","#0984e3","#fd79a8","#e84393","#7c5ce7","#fd79a8","#f9a825","#e84393","#7c5ce7","#0984e3","#fd79a8","#0984e3","#e84393","#fd79a8","#7c5ce7","#f9a825","#fd79a8","#0984e3","#7c5ce7","#e84393","#00b894","#f9a825","#fd79a8","#00b894","#0984e3","#7c5ce7","#fd79a8","#e84393","#f9a825","#0984e3","#7c5ce7","#fd79a8","#e84393","#00b894","#7c5ce7","#fd79a8","#0984e3","#e84393","#7c5ce7"];
const MOVES=["無限先延ばし","深夜のひらめき","課金カタルシス","布団バリア","焚き火ヒーリング","ググり連撃","推しパワー全開","SNS読心術","サブスク忘却","積ん読の知恵","カフェイン三連","二度寝の覇道","ドライブ瞑想","Amazonワンクリック","エナドリ三連星","映えショット","締め切りバースト","感情的深夜ポスト","寝坊フル加速","サウナ整い","ポイント大量回収","無限スクロール","ガチャ五連撃","限界突破トレーニング","Notionページ爆造","満腹全回復","朝5時宣言","リール無限再生","深夜スタバ陣取り","全チャット既読スルー","ワンタップ課金","旅行計画策定"];
const TITLES=['見習い','一般','熟練','精鋭','達人','伝説','神話'];
const ST_KEYS=['hp','int','pay','solo','mot','luk'];

function hash(s){let h=0;for(let i=0;i<s.length;i++){h=((h<<5)-h)+s.charCodeAt(i);h|=0;}return Math.abs(h);}
function sr(seed){let s=seed;return()=>{s=(s*16807)%2147483647;return(s-1)/2147483646;};}
function genOG(name){
  const dateStr=new Date(Date.now()+9*60*60*1000).toDateString();
  const h=hash(name+dateStr),r=sr(h);
  const ji=Math.floor(r()*JOBS.length);
  r();                                   // traits skip
  const mi=Math.floor(r()*MOVES.length);
  r();                                   // wk skip
  r();                                   // qt skip
  let total=0;
  ST_KEYS.forEach(()=>{
    let v=Math.floor(r()*800)+100;
    if(r()>.55)v=Math.floor(r()*400)+800;
    if(r()>.82)v=Math.floor(r()*30)+1;
    if(r()>.97)v=-1;
    if(r()>.993)v=Math.floor(r()*9000)+1000;
    total+=(v>0?v:500);
  });
  const lv=Math.min(99,Math.max(1,Math.floor(total/80)));
  const ti=total<1500?0:total<2000?1:total<2800?2:total<3600?3:total<4500?4:total<6000?5:6;
  return {job:JOBS[ji],jobC:JOBC[ji],lv,title:TITLES[ti],move:MOVES[mi]};
}

function h(type, props, ...children) {
  return {
    type,
    props: {
      ...props,
      children: children.length===0 ? undefined : children.length===1 ? children[0] : children,
    },
  };
}

export default async function handler(req) {
  try {
    const {searchParams} = new URL(req.url);
    const name = searchParams.get('n') || '冒険者';
    const d = genOG(name);
    const jc = d.jobC;

    const imgRes = new ImageResponse(
      h('div', {
        style: {
          width:'1200px', height:'630px', display:'flex', flexDirection:'column',
          alignItems:'center', justifyContent:'center', position:'relative', overflow:'hidden',
          background:'linear-gradient(135deg, #faf5ff 0%, #e8ddf5 100%)',
        }
      },
        // 上部カラーバー
        h('div', {style:{position:'absolute',top:0,left:0,right:0,height:'8px',display:'flex',
          background:'linear-gradient(90deg,#ff8c42,#fd79a8,#7c5ce7,#00b894)'}}),
        // 装飾円
        h('div', {style:{position:'absolute',top:'-80px',right:'-80px',width:'320px',height:'320px',
          borderRadius:'50%',background:'rgba(124,92,231,0.07)',display:'flex'}}),
        h('div', {style:{position:'absolute',bottom:'-60px',left:'-60px',width:'260px',height:'260px',
          borderRadius:'50%',background:'rgba(255,140,66,0.07)',display:'flex'}}),
        // ギルドラベル
        h('div', {style:{fontSize:'20px',color:'#8a7aaa',letterSpacing:'0.12em',marginBottom:'16px',display:'flex'}},
          '冒険者ギルド登録結果'
        ),
        // 名前
        h('div', {style:{
          fontSize: name.length>10 ? '52px' : name.length>6 ? '66px' : '80px',
          fontWeight:700, color:'#2a2040',
          letterSpacing:'0.04em', lineHeight:1.1, marginBottom:'12px', display:'flex'
        }}, name),
        // ジョブ
        h('div', {style:{fontSize:'40px',fontWeight:700,color:jc,
          letterSpacing:'0.06em',marginBottom:'24px',display:'flex'}},
          '【'+d.job+'】'
        ),
        // レベル・称号
        h('div', {style:{display:'flex',gap:'16px',alignItems:'center',marginBottom:'30px'}},
          h('div', {style:{
            background:'rgba(124,92,231,0.1)', border:'2px solid rgba(124,92,231,0.25)',
            borderRadius:'14px', padding:'10px 28px', fontSize:'30px', fontWeight:700, color:'#7c5ce7', display:'flex'
          }}, 'Lv.'+d.lv),
          h('div', {style:{
            background:'rgba(124,92,231,0.06)', border:'2px solid rgba(124,92,231,0.18)',
            borderRadius:'14px', padding:'10px 28px', fontSize:'26px', fontWeight:700, color:'#7c5ce7', display:'flex'
          }}, d.title+'級冒険者')
        ),
        // 必殺技
        h('div', {style:{
          background:'rgba(253,121,168,0.08)', border:'2px solid rgba(253,121,168,0.22)',
          borderRadius:'16px', padding:'16px 40px',
          display:'flex', flexDirection:'column', alignItems:'center', marginBottom:'36px'
        }},
          h('div', {style:{fontSize:'17px',color:'#fd79a8',letterSpacing:'0.12em',marginBottom:'8px',display:'flex'}},
            '必殺技'
          ),
          h('div', {style:{fontSize:'32px',fontWeight:700,color:'#fd79a8',display:'flex'}},
            '「'+d.move+'」'
          )
        ),
        // フッター
        h('div', {style:{position:'absolute',bottom:'26px',
          fontSize:'19px',color:'#9a8aba',letterSpacing:'0.05em',display:'flex'}},
          'ai-life-status.vercel.app'
        )
      ),
      {width:1200, height:630}
    );

    const buf = await imgRes.arrayBuffer();
    if (buf.byteLength === 0) {
      return new Response('render failed: empty buffer', {status:500, headers:{'Content-Type':'text/plain'}});
    }
    return new Response(buf, {
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=86400, s-maxage=86400',
      },
    });
  } catch(e) {
    return new Response('ERROR: '+e.message, {status:500, headers:{'Content-Type':'text/plain'}});
  }
}
