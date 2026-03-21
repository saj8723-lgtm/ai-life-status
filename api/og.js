// Vercel Edge Function — パーソナライズOGP画像生成 (1200x630)
export const config = { runtime: 'edge' };
import { ImageResponse } from '@vercel/og';

const JOBS=["伝説の社畜","深夜のコンビニ賢者","布団の守護神","カフェイン魔術師","散財の錬金術師","孤高のソロキャンパー","妄想の建築家","通知の奴隷","AI魔法剣士","深夜ラーメン背徳者","ドライブの哲学者","推し活の聖女","副業沼の冒険者","永遠の計画マン","カフェ巡りの魔女","ストーリーズの女神","コスメ錬金術師","積ん読の大賢者","昼寝の大魔王","サブスク放置の貴族","推しの騎士","深夜アニメの求道者","Google検索の勇者","タピオカの巫女","Zoom疲れの勇者","TikTok沼の住人","推し活破産者","深夜Xの亡者","週末シェフ見習い","寝落ち配信の伴走者","ガジェット沼の住人","名言コレクターの賢者","筋トレ伝道師","サウナ道の求道者","ポイ活の大魔導士","終電ダッシュの勇者","有給消化の忍者","スタバ常駐の文豪","キャンプ装備コレクター","朝活宣言の戦士","自炊失敗の料理見習い","写真フォルダ整理師","ミーティング生存者","一気見配信の探偵","ガチャ沼の錬金術師","深夜筋トレの修行僧","週末旅人の吟遊詩人","ポッドキャスト中毒者","締め切り破壊神","Notion設計師","朝ラン失踪者","リール収集の魔術師"];
const JOBC=["#e84393","#7c5ce7","#fd79a8","#0984e3","#f9a825","#00b894","#7c5ce7","#fd79a8","#0984e3","#e84393","#7c5ce7","#fd79a8","#f9a825","#00b894","#0984e3","#fd79a8","#e84393","#7c5ce7","#fd79a8","#f9a825","#e84393","#7c5ce7","#0984e3","#fd79a8","#0984e3","#e84393","#fd79a8","#7c5ce7","#f9a825","#fd79a8","#0984e3","#7c5ce7","#e84393","#00b894","#f9a825","#fd79a8","#00b894","#0984e3","#7c5ce7","#fd79a8","#e84393","#f9a825","#0984e3","#7c5ce7","#fd79a8","#e84393","#00b894","#7c5ce7","#fd79a8","#0984e3","#e84393","#7c5ce7"];
const MOVES=["無限先延ばし","深夜のひらめき","課金カタルシス","布団バリア","焚き火ヒーリング","ググり連撃","推しパワー全開","SNS読心術","サブスク忘却","積ん読の知恵","カフェイン三連","二度寝の覇道","ドライブ瞑想","Amazonワンクリック","エナドリ三連星","映えショット","締め切りバースト","感情的深夜ポスト","寝坊フル加速","サウナ整い","ポイント大量回収","無限スクロール","ガチャ五連撃","限界突破トレーニング","Notionページ爆造","満腹全回復","朝5時宣言","リール無限再生","深夜スタバ陣取り","全チャット既読スルー","ワンタップ課金","旅行計画策定"];
const WKS=["月曜朝: 全ステ-50%（呪いは日曜夜23時から始まる）","「あと5分」→30分バグ（完治例ゼロ）","Amazonレコメンドが急所を突いてくる（防御不能）","ドラマ最終話前でやめられない病（全予定キャンセル）","布団引力: 起床判定に5回失敗すると二度寝確定","充電5%警告: 焦りで全ステ-40%（充電中は回復）","無料配送まで△円: 必ず余計なものを買ってしまう","「もう寝る」宣言後2時間はスマホをやめられない","深夜の飯テロ: 食欲+9999（睡眠妨害・解呪不能）","既読スルーされると考察が止まらない（知力-70%）","推しのツアー発表: 課金ブレーキ消滅（財布は戦場）","エナドリ切れ: 知力半減（補充まで人権なし）","セール通知: 理性が5分だけ消える（5分で十分）","「ちょっとだけゲーム」→気づいたら朝（睡眠ゼロ）","新しい沼を発見した瞬間: 全貯金が危険にさらされる","他人のキラキラ投稿: HP-10（毎日累積ダメージ）","返信は「あとで」→72時間経過バグ（相手のHPも減る）","コンビニに入ると予算の2倍使って出てくる（金運-200）","「1曲だけ」→気づいたら全アルバム制覇（時間消滅）","SNSで有益情報を保存→満足して一度も見返さない","既読無視した罪悪感でHP-20（返信するまで毎時間続く）","グループLINE未読999: 永遠に開けない恐怖（孤独耐性-50%）"];
const TITLES=['見習い','一般','熟練','精鋭','達人','伝説','神話'];
const ST=[
  {n:'💪',k:'hp', c:'#e84393',lb:'体力'},
  {n:'🧠',k:'int',c:'#0984e3',lb:'知力'},
  {n:'💰',k:'pay',c:'#f9a825',lb:'金運'},
  {n:'😎',k:'solo',c:'#7c5ce7',lb:'孤独'},
  {n:'🔥',k:'mot',c:'#fd79a8',lb:'やる気'},
  {n:'🍀',k:'luk',c:'#00b894',lb:'運'},
];

function hash(s){let h=0;for(let i=0;i<s.length;i++){h=((h<<5)-h)+s.charCodeAt(i);h|=0;}return Math.abs(h);}
function sr(seed){let s=seed;return()=>{s=(s*16807)%2147483647;return(s-1)/2147483646;};}

function genOG(name){
  const dateStr=new Date(Date.now()+9*60*60*1000).toDateString();
  const hv=hash(name+dateStr),r=sr(hv);
  const ji=Math.floor(r()*JOBS.length);
  r();
  const mi=Math.floor(r()*MOVES.length);
  const wi=Math.floor(r()*WKS.length);
  r();
  const sv={};let total=0;
  ST.forEach(s=>{
    let v=Math.floor(r()*800)+100;
    if(r()>.55)v=Math.floor(r()*400)+800;
    if(r()>.82)v=Math.floor(r()*30)+1;
    if(r()>.97)v=-1;
    if(r()>.993)v=Math.floor(r()*9000)+1000;
    sv[s.k]=v;total+=(v>0?v:500);
  });
  const lv=Math.min(99,Math.max(1,Math.floor(total/80)));
  const ti=total<1500?0:total<2000?1:total<2800?2:total<3600?3:total<4500?4:total<6000?5:6;
  return {job:JOBS[ji],jobC:JOBC[ji],lv,title:TITLES[ti],move:MOVES[mi],wk:WKS[wi],sv};
}

function radarPts(sv,cx,cy,R){
  const MAX=1200;
  return ST.map((s,i)=>{
    const angle=(i*60-90)*Math.PI/180;
    const val=sv[s.k]<0?R*1.15:Math.min(sv[s.k]/MAX,1.15)*R;
    return `${(cx+val*Math.cos(angle)).toFixed(1)},${(cy+val*Math.sin(angle)).toFixed(1)}`;
  }).join(' ');
}
function gridPts(frac,cx,cy,R){
  return ST.map((_,i)=>{
    const angle=(i*60-90)*Math.PI/180;
    const r=R*frac;
    return `${(cx+r*Math.cos(angle)).toFixed(1)},${(cy+r*Math.sin(angle)).toFixed(1)}`;
  }).join(' ');
}

function h(type,props,...children){
  return{type,props:{...props,children:children.length===0?undefined:children.length===1?children[0]:children}};
}

export default async function handler(req){
  try{
    const {searchParams}=new URL(req.url);
    const name=searchParams.get('n')||'冒険者';
    const d=genOG(name);
    const jc=d.jobC;

    // レーダーチャート設定
    // SVGサイズ 380×360, 中心 cx=190 cy=180, R=115
    // ラベル位置 labelR=151 → 全ラベルに余白あり（確認済み）
    const cx=190,cy=180,R=115;
    const dataPts=radarPts(d.sv,cx,cy,R);
    const axes=ST.map((_,i)=>{
      const angle=(i*60-90)*Math.PI/180;
      return h('line',{
        x1:String(cx),y1:String(cy),
        x2:String((cx+R*Math.cos(angle)).toFixed(1)),
        y2:String((cy+R*Math.sin(angle)).toFixed(1)),
        stroke:'rgba(124,92,231,0.3)',strokeWidth:'1.5',
      });
    });
    const grids=[0.25,0.5,0.75,1].map(f=>
      h('polygon',{points:gridPts(f,cx,cy,R),fill:'none',stroke:'rgba(124,92,231,0.18)',strokeWidth:'1'})
    );

    // HTML ラベル（絵文字 + 日本語）— SVG 座標系と同じ原点で絶対配置
    const labelR=R+36;
    const htmlLabels=ST.map((s,i)=>{
      const angle=(i*60-90)*Math.PI/180;
      const lx=Math.round(cx+labelR*Math.cos(angle));
      const ly=Math.round(cy+labelR*Math.sin(angle));
      return h('div',{style:{
        position:'absolute',
        left:String(lx-26)+'px',
        top: String(ly-22)+'px',
        width:'52px',
        display:'flex',flexDirection:'column',alignItems:'center',
      }},
        h('div',{style:{fontSize:'22px',lineHeight:'1.1',display:'flex'}},s.n),
        h('div',{style:{fontSize:'11px',color:s.c,fontWeight:'700',lineHeight:'1.2',display:'flex'}},s.lb)
      );
    });

    return new ImageResponse(
      h('div',{style:{
        width:'1200px',height:'630px',display:'flex',flexDirection:'column',
        position:'relative',overflow:'hidden',
        background:'linear-gradient(135deg,#faf5ff 0%,#e8ddf5 100%)',
      }},
        // 上部カラーバー
        h('div',{style:{position:'absolute',top:0,left:0,right:0,height:'7px',display:'flex',
          background:'linear-gradient(90deg,#ff8c42,#fd79a8,#7c5ce7,#00b894)'}}),
        // 装飾円（背景）
        h('div',{style:{position:'absolute',top:'-60px',right:'-60px',width:'240px',height:'240px',
          borderRadius:'50%',background:'rgba(124,92,231,0.07)',display:'flex'}}),
        h('div',{style:{position:'absolute',bottom:'-40px',left:'-40px',width:'180px',height:'180px',
          borderRadius:'50%',background:'rgba(255,140,66,0.07)',display:'flex'}}),

        // メインコンテンツ（左カラム 530px ＋ 右カラム flex:1）
        h('div',{style:{
          display:'flex',flex:1,
          paddingTop:'18px',paddingRight:'28px',paddingBottom:'40px',paddingLeft:'28px',
          gap:'24px',marginTop:'7px',
        }},

          // ===== 左カラム =====
          h('div',{style:{display:'flex',flexDirection:'column',width:'510px',flexShrink:0,justifyContent:'center'}},

            // ギルドラベル
            h('div',{style:{fontSize:'13px',color:'#8a7aaa',letterSpacing:'0.1em',marginBottom:'8px',display:'flex'}},
              '✦ 冒険者ギルド登録結果 ✦'
            ),
            // 名前
            h('div',{style:{
              fontSize:name.length>8?'46px':name.length>5?'56px':'68px',
              fontWeight:700,color:'#2a2040',letterSpacing:'0.03em',
              lineHeight:'1.1',marginBottom:'6px',display:'flex',
            }},name),
            // ジョブ
            h('div',{style:{fontSize:'24px',fontWeight:700,color:jc,
              letterSpacing:'0.05em',marginBottom:'12px',display:'flex'}},
              '【'+d.job+'】'
            ),
            // Lv + 称号
            h('div',{style:{display:'flex',gap:'8px',alignItems:'center',marginBottom:'14px'}},
              h('div',{style:{
                background:'rgba(124,92,231,0.1)',border:'1.5px solid rgba(124,92,231,0.3)',
                borderRadius:'8px',paddingTop:'4px',paddingBottom:'4px',paddingLeft:'14px',paddingRight:'14px',
                fontSize:'20px',fontWeight:700,color:'#7c5ce7',display:'flex',
              }},'Lv.'+d.lv),
              h('div',{style:{
                background:'rgba(124,92,231,0.06)',border:'1.5px solid rgba(124,92,231,0.2)',
                borderRadius:'8px',paddingTop:'4px',paddingBottom:'4px',paddingLeft:'14px',paddingRight:'14px',
                fontSize:'16px',fontWeight:700,color:'#7c5ce7',display:'flex',
              }},d.title+'級冒険者')
            ),
            // 必殺技
            h('div',{style:{
              background:'rgba(253,121,168,0.08)',border:'1.5px solid rgba(253,121,168,0.25)',
              borderRadius:'10px',
              paddingTop:'9px',paddingBottom:'9px',paddingLeft:'14px',paddingRight:'14px',
              marginBottom:'10px',display:'flex',flexDirection:'column',
            }},
              h('div',{style:{fontSize:'11px',color:'#fd79a8',letterSpacing:'0.1em',marginBottom:'3px',display:'flex'}},'⚡ 必殺技'),
              h('div',{style:{fontSize:'19px',fontWeight:700,color:'#fd79a8',display:'flex'}},'「'+d.move+'」')
            ),
            // 弱点（全文表示）
            h('div',{style:{
              background:'rgba(42,32,64,0.04)',border:'1.5px solid rgba(42,32,64,0.1)',
              borderRadius:'8px',
              paddingTop:'8px',paddingBottom:'8px',paddingLeft:'12px',paddingRight:'12px',
              display:'flex',flexDirection:'column',
            }},
              h('div',{style:{fontSize:'11px',color:'#8a7aaa',letterSpacing:'0.08em',marginBottom:'3px',display:'flex'}},'🛡 弱点'),
              h('div',{style:{fontSize:'14px',color:'#5a4a7a',lineHeight:'1.5',display:'flex',flexWrap:'wrap'}},d.wk)
            )
          ),

          // ===== 右カラム（レーダーチャート）=====
          h('div',{style:{
            display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',
            flex:1,
          }},
            h('div',{style:{fontSize:'12px',color:'#8a7aaa',letterSpacing:'0.1em',marginBottom:'4px',display:'flex'}},
              'ステータス'
            ),
            // SVG + HTMLラベル を重ねるコンテナ（380×360）
            h('div',{style:{position:'relative',width:'380px',height:'360px',display:'flex'}},
              h('svg',{width:'380',height:'360',viewBox:'0 0 380 360'},
                ...grids,
                ...axes,
                h('polygon',{
                  points:dataPts,
                  fill:'rgba(124,92,231,0.22)',
                  stroke:'#7c5ce7',
                  strokeWidth:'2.5',
                })
              ),
              ...htmlLabels
            )
          )
        ),

        // フッター
        h('div',{style:{
          position:'absolute',bottom:'12px',right:'28px',
          fontSize:'13px',color:'#9a8aba',letterSpacing:'0.04em',display:'flex',
        }},'ai-life-status.vercel.app')
      ),
      {width:1200,height:630}
    );
  }catch(e){
    return new Response('ERROR: '+e.message,{status:500,headers:{'Content-Type':'text/plain'}});
  }
}
