import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, interpolate} from 'remotion';

type Scene = {heading: string; caption: string};
export type ZombieProps = {
  title: string;
  subtitle: string;
  background: string;
  accent: string;
  scenes: Scene[];
  kind?: string;
  hasVoice?: boolean;
};

const W=720, H=1280;
const duration=40*30;
const timing=[
  {from:0,to:150,label:'18:47 · MI CASA',say:'Todo empezó como una tarde cualquiera...'},
  {from:150,to:300,label:'SEÑAL DE EMERGENCIA',say:'Hasta que llegó la primera alerta.'},
  {from:300,to:495,label:'LA CALLE',say:'Me asomé... y vi cómo la ciudad se venía abajo.'},
  {from:495,to:660,label:'NO ERAN PERSONAS',say:'Algo estaba persiguiendo a mis vecinos.'},
  {from:660,to:840,label:'TRES GOLPES',say:'Entonces alguien golpeó la puerta.'},
  {from:840,to:975,label:'SIN TIEMPO',say:'Solo me quedaban segundos para decidir.'},
  {from:975,to:1200,label:'DECIDE TÚ',say:''},
];
const clamp=(n:number,a=0,b=1)=>Math.max(a,Math.min(b,n));
const lerp=(a:number,b:number,x:number)=>a+(b-a)*x;
const fade=(frame:number,start:number,end:number)=>clamp((frame-start)/Math.max(1,end-start));
const rain=Array.from({length:78},(_,i)=>({x:(i*149+57)%730,y:(i*373+26)%1340,len:19+i%5*12,speed:11+i%7*2}));
const facade=Array.from({length:14},(_,i)=>({x:i*61-25,h:95+(i*89)%300,w:44+(i*19)%46}));
const walk=Array.from({length:6},(_,i)=>({x:92+i*110,y:730+(i%3)*22,s:0.56+(i%3)*0.2}));

const FilmGrain:React.FC<{f:number;flash?:boolean}>=({f,flash=false})=>{
 const a=((f*37)%101)/101;
 return <AbsoluteFill style={{pointerEvents:'none',mixBlendMode:'screen'}}>
  <div style={{position:'absolute',inset:0,background:'repeating-linear-gradient(0deg,transparent 0px,transparent 4px,#e5ecff08 5px)',opacity:.62}}/>
  <div style={{position:'absolute',inset:0,boxShadow:'inset 0 0 185px #000c, inset 0 0 420px #0009'}}/>
  <div style={{position:'absolute',left:(a*W),top:0,width:2,height:H,background:'#fff',opacity:(f%109===0)?0.12:0}}/>
  {flash&&f%143<3?<div style={{position:'absolute',inset:0,background:'#e5f4ff',opacity:0.17}}/>:null}
 </AbsoluteFill>;
};

const Rain:React.FC<{f:number;strength?:number}>=({f,strength=1})=><svg width={W} height={H} viewBox="0 0 720 1280" style={{position:'absolute',inset:0,opacity:.44*strength}}>
 {rain.map((d,i)=><line key={i} x1={d.x} y1={(d.y+f*d.speed)%1390-80} x2={d.x-11} y2={(d.y+f*d.speed)%1390+d.len-80} stroke={i%5===0?'#d9edf6':'#80a7b7'} strokeWidth={i%9===0?2:1}/>)}
 </svg>;

const Figure:React.FC<{scale?:number;zombie?:boolean;lean?:number;f?:number}>=({scale=1,zombie=false,lean=0,f=0})=>
 <svg viewBox="0 0 120 320" width={120*scale} height={320*scale} style={{overflow:'visible',filter:'drop-shadow(0 6px 17px #000a)',transform:'rotate('+(lean+Math.sin(f/10)*1.5)+'deg)'}}>
  <ellipse cx="60" cy="53" rx="36" ry="48" fill={zombie?'#232e2e':'#101820'}/>
  <path d="M28 55 Q20 8 59 0 Q105 0 97 56 L82 32 L37 33 Z" fill="#090e14"/>
  <rect x="47" y="85" width="28" height="26" rx="8" fill="#151e25"/>
  <path d="M16 114 Q23 96 60 100 Q100 96 108 120 L112 234 L8 234Z" fill={zombie?'#23302d':'#172531'}/>
  <path d="M38 105 Q62 145 86 105 L68 230 L48 230Z" fill={zombie?'#172421':'#263b4b'}/>
  <path d="M17 119 Q-9 153 16 220" stroke={zombie?'#25332e':'#1d2d38'} strokeWidth="24" fill="none" strokeLinecap="round"/>
  <path d="M104 124 Q129 164 105 214" stroke={zombie?'#28372f':'#1c2c38'} strokeWidth="24" fill="none" strokeLinecap="round"/>
  <path d="M31 232 L22 310 M83 232 L91 310" stroke="#111c23" strokeWidth="32" strokeLinecap="round"/>
  {zombie&&<><circle cx="47" cy="56" r="5" fill="#ff4c4c"/><circle cx="76" cy="56" r="5" fill="#ff4c4c"/><path d="M44 82 L80 85" stroke="#8b2229" strokeWidth="4"/></>}
 </svg>;

const City:React.FC<{f:number;close?:boolean}>=({f,close=false})=>{
 const move=close?18*Math.sin(f/40):0;
 return <AbsoluteFill style={{overflow:'hidden',background:'linear-gradient(#0a121c 8%,#152936 58%,#32484b 80%,#0b1218 100%)'}}>
  <div style={{position:'absolute',width:570,height:570,left:70,top:72,borderRadius:'50%',background:'#a8b4ad',filter:'blur(67px)',opacity:.12}}/>
  <div style={{position:'absolute',left:-30,top:340,width:800,height:400,background:'linear-gradient(transparent,#6b76714b 90%)',filter:'blur(22px)'}}/>
  <svg width={W} height={H} style={{position:'absolute'}}>
   <g transform={'translate('+move+' 0)'}>
   {facade.map((b,i)=><g key={i}>
     <rect x={b.x} y={696-b.h} width={b.w} height={b.h+265} fill={i%2===0?'#0e1923':'#162532'}/>
     {Array.from({length:5},(_,j)=><rect key={j} x={b.x+8+(j%2)*19} y={716-b.h+Math.floor(j/2)*46} width="9" height="14" fill={i%3===0&&j%2===0?'#d5b276':'#3d5761'} opacity={i%3===0?.5:.2}/>)}
   </g>)}
   <path d="M0 850 L720 790 L720 1280 L0 1280 Z" fill="#121a22"/>
   <path d="M0 891 L720 823" stroke="#505d5c" strokeWidth="10"/>
   <path d="M160 1050 L270 1028 M405 1004 L534 978" stroke="#7e867a" strokeWidth="7" strokeDasharray="50 20" opacity=".24"/>
   <path d="M600 436 L604 851" stroke="#18232b" strokeWidth="14"/><path d="M603 459 L677 479" stroke="#1f3037" strokeWidth="9"/><ellipse cx="674" cy="479" rx="46" ry="15" fill="#f6a46b" opacity=".32"/>
   <path d="M460 898 L523 898 L559 950 L465 950Z" fill="#181d22"/>
   <rect x="475" y="871" width="68" height="49" rx="16" fill="#28313a"/><rect x="487" y="880" width="43" height="19" fill="#9db5aa" opacity=".27"/>
   {walk.map((p,i)=><g key={i} transform={'translate('+(p.x+Math.sin(f/15+i)*17)+' '+(p.y+Math.cos(f/16+i)*6)+') scale('+p.s+')'}><Figure zombie={i%2===0} lean={i%2===0?12:-7} f={f}/></g>)}
   </g>
  </svg>
  <Rain f={f} strength={1.4}/>
  <div style={{position:'absolute',inset:0,background:'linear-gradient(0deg,#02060cdd,transparent 40%,#060a16ad)',pointerEvents:'none'}}/>
 </AbsoluteFill>;
};

const Room:React.FC<{f:number;tv?:boolean;windowFocus?:boolean}>=({f,tv=false,windowFocus=false})=>{
 const zoom=windowFocus?1.12:1+f*0.000045;
 return <AbsoluteFill style={{background:'#15242b'}}>
  <AbsoluteFill style={{transform:'scale('+zoom+') translateX('+((windowFocus?-18:0)+Math.sin(f/67)*3)+'px)',transformOrigin:'center center'}}>
   <City f={f}/>
   <div style={{position:'absolute',left:-12,top:-10,width:145,height:1340,background:'#161d23',boxShadow:'25px 0 40px #0008'}}/>
   <div style={{position:'absolute',right:-11,top:-10,width:145,height:1340,background:'#141b20',boxShadow:'-25px 0 40px #0008'}}/>
   <div style={{position:'absolute',top:0,left:0,right:0,height:230,background:'#1c2329',boxShadow:'0 30px 60px #0009'}}/>
   <div style={{position:'absolute',left:118,top:228,width:484,height:825,border:'31px solid #1e272e',boxShadow:'0 0 55px #000 inset, 0 0 28px #000c'}}/>
   <div style={{position:'absolute',left:350,top:228,width:21,height:825,background:'#25343c'}}/>
   <div style={{position:'absolute',left:118,top:635,width:484,height:18,background:'#2a333a'}}/>
   <div style={{position:'absolute',bottom:0,width:'100%',height:255,background:'linear-gradient(#24252a,#121820)'}}/>
   <div style={{position:'absolute',left:30,top:875,width:302,height:198,borderRadius:'28px 28px 9px 9px',background:'#1b272d',boxShadow:'14px -6px 22px #0008'}}/>
   <div style={{position:'absolute',left:44,top:1030,width:325,height:40,background:'#0d161c'}}/>
   <div style={{position:'absolute',right:18,top:924,width:230,height:139,background:'#060d12',border:'14px solid #1b2024',borderRadius:5,boxShadow:'0 0 34px #ff453522'}}/>
   <div style={{position:'absolute',right:39,top:946,width:186,height:93,background:tv?'#8d1d29':'#203d45',display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'column',color:'#faf0e0'}}>
     {tv?<><span style={{fontSize:12,letterSpacing:2,fontWeight:900}}>EMERGENCIA</span><span style={{fontSize:10,marginTop:6}}>NO SALGA DE SU CASA</span></>:<span style={{fontSize:12,opacity:.7}}>NOTICIAS 24</span>}
   </div>
   <div style={{position:'absolute',left:270,bottom:0,transform:'scale(2.3)',transformOrigin:'bottom center'}}><Figure f={f}/></div>
  </AbsoluteFill>
  <FilmGrain f={f} flash={true}/>
 </AbsoluteFill>;
};

const TV:React.FC<{f:number}>=({f})=><AbsoluteFill style={{background:'#080e12'}}>
 <div style={{position:'absolute',left:-60,top:170,width:840,height:870,borderRadius:30,border:'32px solid #1a2127',background:'#610f1c',boxShadow:'0 0 100px #9a2b3b44,inset 0 0 95px #0008',transform:'rotate('+Math.sin(f/24)*.6+'deg) scale('+(1+f*.00032)+')'}}>
  <div style={{position:'absolute',inset:20,background:'linear-gradient(145deg,#731d2b,#ad2936 55%,#4f1526)',display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'column',gap:30}}>
   <div style={{fontSize:31,letterSpacing:7,fontWeight:900,color:'#fff'}}>TRANSMISIÓN DE</div>
   <div style={{fontSize:86,fontWeight:1000,lineHeight:.98,letterSpacing:-3,color:'#fff',textAlign:'center'}}>ALERTA<br/>NACIONAL</div>
   <div style={{height:9,width:370,background:'#f4ead8'}}/>
   <div style={{fontWeight:700,fontSize:35,color:'#fff',textAlign:'center',letterSpacing:3}}>REFÚGIESE EN SU HOGAR</div>
   <div style={{position:'absolute',bottom:50,left:20,right:20,height:85,background:'#0d161ee8',display:'flex',alignItems:'center',justifyContent:'center',color:'#fff',fontSize:26,fontWeight:700}}>ATAQUES EN DISTINTAS ZONAS</div>
  </div>
  <div style={{position:'absolute',inset:0,background:'repeating-linear-gradient(0deg,#ffffff00 0px,#ffffff00 5px,#ffffff22 6px)',opacity:.21,pointerEvents:'none'}}/>
 </div>
 <div style={{position:'absolute',left:34,top:1142,color:'#fdb7b7',fontSize:20,letterSpacing:3,fontWeight:800}}>SEÑAL INTERRUMPIDA · 18:51</div>
 <FilmGrain f={f} flash/>
 </AbsoluteFill>;

const WindowScene:React.FC<{f:number;close?:boolean}>=({f,close=false})=><AbsoluteFill>
 <City f={f} close={close}/>
 <div style={{position:'absolute',left:0,top:0,width:34,height:'100%',background:'#081015',boxShadow:'22px 0 30px #000b'}}/>
 <div style={{position:'absolute',right:0,top:0,width:31,height:'100%',background:'#091017',boxShadow:'-22px 0 30px #000b'}}/>
 {!close&&<><div style={{position:'absolute',left:347,top:0,width:22,height:1280,background:'#0b151b'}}/><div style={{position:'absolute',left:0,top:530,height:19,width:720,background:'#0d1821'}}/></>}
 <div style={{position:'absolute',inset:0,background:'linear-gradient(90deg,#05080fc9,transparent 25%,transparent 75%,#05080fc1)'}}/>
 {close&&<><div style={{position:'absolute',left:52,top:500,transform:'scale(2.2) rotate(-2deg)',opacity:.77}}><Figure zombie f={f}/></div><div style={{position:'absolute',right:24,top:710,transform:'scale(2.6)',opacity:.83}}><Figure zombie f={f+20}/></div></>}
 <FilmGrain f={f} flash/>
 </AbsoluteFill>;

const Door:React.FC<{f:number}>=({f})=>{
 const knock=(f%63<6)?Math.sin(f*1.8)*10:0;
 return <AbsoluteFill style={{background:'linear-gradient(120deg,#0b171b,#26333a 65%,#0d1a24)'}}>
  <div style={{position:'absolute',left:48,top:90,width:624,height:1130,background:'#12181f',boxShadow:'0 0 60px #000 inset',border:'17px solid #26343d'}}/>
  <div style={{position:'absolute',left:103+knock,top:148,width:505,height:1055,background:'linear-gradient(100deg,#2b353b,#141e28 60%,#273337)',border:'5px solid #374a51',boxShadow:'inset 0 0 120px #0008'}}/>
  <div style={{position:'absolute',left:140+knock,top:226,width:430,height:380,border:'8px solid #29363e',boxShadow:'inset 0 0 40px #0008'}}/>
  <div style={{position:'absolute',left:140+knock,top:675,width:430,height:360,border:'8px solid #29363e',boxShadow:'inset 0 0 40px #0008'}}/>
  <div style={{position:'absolute',right:130-knock,top:743,width:90,height:25,borderRadius:15,background:'#889497',boxShadow:'0 0 17px #e4f3ff44'}}/>
  <div style={{position:'absolute',right:167-knock,top:719,width:33,height:33,borderRadius:'50%',background:'#a8b5b9'}}/>
  <div style={{position:'absolute',left:50,bottom:0,width:620,height:125,background:'#02070b'}}/>
  <div style={{position:'absolute',left:145,top:170,width:445,height:980,background:'#b4111930',opacity:f%63<9?.6:.05}}/>
  <div style={{position:'absolute',left:90,top:160,right:90,color:'#dbe9f0',fontSize:24,letterSpacing:4,textAlign:'center',fontWeight:800}}>¿QUIÉN ESTÁ AFUERA?</div>
  <FilmGrain f={f} flash={f%63<7}/>
 </AbsoluteFill>;
};

const Bag:React.FC<{f:number}>=({f})=><AbsoluteFill style={{background:'radial-gradient(ellipse at 60% 48%,#4f5549,#111b21 66%,#04080d)'}}>
 <div style={{position:'absolute',top:275,left:-50,width:830,height:730,background:'#243136',transform:'rotate(-9deg)',boxShadow:'0 0 80px #0008'}}/>
 <div style={{position:'absolute',left:160,top:435,width:430,height:560,borderRadius:'155px 145px 62px 65px',background:'linear-gradient(115deg,#182a31,#34444a 55%,#101a22)',boxShadow:'inset 35px 8px 48px #0008,0 20px 40px #0009',transform:'rotate('+Math.sin(f/18)*1.8+'deg)'}}/>
 <div style={{position:'absolute',left:265,top:375,width:220,height:112,border:'23px solid #1a292d',borderBottom:'none',borderRadius:'85px 85px 0 0'}}/>
 <div style={{position:'absolute',left:240,top:685,width:286,height:173,borderRadius:25,background:'#25363b',boxShadow:'inset 0 0 19px #0008',border:'9px solid #1b2c33'}}/>
 <div style={{position:'absolute',left:356,top:682,width:38,height:183,background:'#101d24',borderRadius:9}}/>
 <div style={{position:'absolute',left:80,top:205,width:164,height:300,background:'#35404a',transform:'rotate(-28deg)',borderRadius:18,boxShadow:'0 0 20px #0005'}}/>
 <div style={{position:'absolute',left:101,top:231,width:121,height:225,background:'#afb7aa',transform:'rotate(-28deg)',borderRadius:8}}/>
 <div style={{position:'absolute',right:74,top:177,width:80,height:286,background:'#697e79',borderRadius:32,transform:'rotate(19deg)'}}/>
 <div style={{position:'absolute',right:92,top:162,width:43,height:23,background:'#99ada7',transform:'rotate(19deg)'}}/>
 <div style={{position:'absolute',left:84,top:1052,color:'#d5e9f2',fontSize:38,fontWeight:900,letterSpacing:2}}>AGUA. LINTERNA. SALIR.</div>
 <FilmGrain f={f}/>
 </AbsoluteFill>;

const Poll:React.FC<{f:number}>=({f})=>{
 const entrance=fade(f,975,1007);const pulse=.7+.3*Math.sin(f*.1);
 return <AbsoluteFill style={{background:'radial-gradient(ellipse at center,#1a3037,#061014 70%,#020609)',color:'#fff'}}>
  <div style={{position:'absolute',left:45,top:115,letterSpacing:7,fontSize:24,fontWeight:900,color:'#9ec7bc'}}>APOCALIPSIS Z · EPISODIO 01</div>
  <div style={{position:'absolute',left:50,top:275,width:620,fontSize:65,lineHeight:1.02,fontWeight:1000,textAlign:'center',letterSpacing:-2,transform:'translateY('+lerp(28,0,entrance)+'px)',opacity:entrance}}>¿QUÉ DEBERÍA<br/>HACER AHORA?</div>
  <div style={{position:'absolute',left:35,top:495,width:650,height:210,border:'4px solid #63ead9',borderRadius:28,boxShadow:'0 0 '+(15*pulse)+'px #63ead944',background:'#0d2c2e',display:'flex',alignItems:'center',gap:32,padding:'25px',boxSizing:'border-box'}}>
   <div style={{fontSize:100,fontWeight:1000,color:'#63ead9'}}>A</div>
   <div style={{display:'flex',flexDirection:'column',gap:12}}><span style={{fontSize:36,fontWeight:900}}>ATRINCHERARME</span><span style={{fontSize:24,color:'#bfd5d1'}}>Resistir dentro de casa</span></div>
  </div>
  <div style={{position:'absolute',left:35,top:733,width:650,height:210,border:'4px solid #f99b70',borderRadius:28,boxShadow:'0 0 '+(15*pulse)+'px #f99b7044',background:'#342019',display:'flex',alignItems:'center',gap:32,padding:'25px',boxSizing:'border-box'}}>
   <div style={{fontSize:100,fontWeight:1000,color:'#ffac79'}}>B</div>
   <div style={{display:'flex',flexDirection:'column',gap:12}}><span style={{fontSize:38,fontWeight:900}}>ESCAPAR</span><span style={{fontSize:24,color:'#e9cdb9'}}>Salir por la puerta trasera</span></div>
  </div>
  <div style={{position:'absolute',left:45,right:45,bottom:130,textAlign:'center',fontWeight:900,fontSize:34,lineHeight:1.18,color:'#ffffff'}}>COMENTA <span style={{color:'#65eddf'}}>A</span> O <span style={{color:'#ffa16d'}}>B</span><br/>Y DECIDE LA SIGUIENTE PARTE</div>
  <div style={{position:'absolute',left:180,right:180,bottom:57,height:4,background:'#6fbbb0',opacity:.45}}/>
  <FilmGrain f={f}/>
 </AbsoluteFill>;
};

const Subtitle:React.FC<{f:number;label:string;say:string;accent?:string}>=({f,label,say,accent='#d8f7ea'})=><>
 <div style={{position:'absolute',left:39,top:75,padding:'10px 17px',background:'#050b11d9',borderLeft:'6px solid #e15252',fontSize:20,fontWeight:850,letterSpacing:3,color:'#e5edf0'}}>{label}</div>
 {say&&<div style={{position:'absolute',left:31,right:31,bottom:137,background:'#020810d9',borderRadius:13,padding:'21px 20px',color:accent,textAlign:'center',fontSize:33,fontWeight:800,lineHeight:1.18,textShadow:'0 2px 4px #000',minHeight:60}}>{say}</div>}
 <div style={{position:'absolute',left:36,right:36,bottom:72,height:3,background:'#a2c2ba44'}}><div style={{height:'100%',width:((f/duration)*100)+'%',background:'#ed6565'}}/></div>
 </>;

const GrainCut:React.FC<{f:number}>=({f})=><div style={{position:'absolute',inset:0,background:'#050a11',opacity:timing.some(t=>Math.abs(f-t.from)<2&&f!==0)?.46:0,pointerEvents:'none'}}/>;

export const ZombieEpisode:React.FC<ZombieProps>=({hasVoice=false,scenes=[]})=>{
 const f=useCurrentFrame();
 let segment=timing.findIndex(t=>f>=t.from&&f<t.to);
 if(segment<0)segment=timing.length-1;
 const s=timing[segment];
 const chapter=f-s.from;
 let visual:React.ReactNode=null;
 if(segment===0)visual=<Room f={f}/>;
 if(segment===1)visual=<TV f={f}/>;
 if(segment===2)visual=<WindowScene f={f}/>;
 if(segment===3)visual=<WindowScene f={f} close/>;
 if(segment===4)visual=<Door f={f}/>;
 if(segment===5)visual=<Bag f={f}/>;
 if(segment===6)visual=<Poll f={f}/>;
 const sceneText=segment<5?scenes[segment]?.caption:'';
 const takeText=sceneText&&sceneText.length>9?sceneText:s.say;
 return <AbsoluteFill style={{fontFamily:'Arial, Helvetica, sans-serif',background:'#03070c',color:'#fff',overflow:'hidden'}}>
  {visual}
  {segment!==6?<Subtitle f={f} label={s.label} say={takeText}/>:null}
  <GrainCut f={f}/>
  <Audio src={staticFile('zombie-ambience.wav')} volume={0.45}/>
  {hasVoice&&timing.slice(0,7).map((t,i)=><Sequence key={i} from={t.from} durationInFrames={t.to-t.from}><Audio src={staticFile('voice-'+i+'.mp3')} volume={1}/></Sequence>)}
  <div style={{position:'absolute',bottom:19,right:27,fontSize:18,letterSpacing:3,color:'#ffffff60'}}>EP 01 · ¿QUÉ HARÍAS?</div>
 </AbsoluteFill>;
};
