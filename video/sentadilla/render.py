import json, math, os, subprocess, wave
from PIL import Image, ImageDraw, ImageFont
P='video/sentadilla/'
S=json.load(open(P+'storyboard.json',encoding='utf-8'))['scenes']
W,H,FPS=540,960,15
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
ft=lambda n,b=False:ImageFont.truetype(bold if b else font,n)
bg='#0c151c'; fg='#f5f7f5'; aqua='#71f2ca'
os.makedirs('out',exist_ok=True)
txt=' '.join(s['voice'] for s in S)
subprocess.run(['espeak','-v','es-la+m3','-s','170','-a','150','-w','out/voice.wav',txt],check=True)
with wave.open('out/voice.wav','rb') as w: duration=w.getnframes()/w.getframerate()+1.5
# Allocate equal visual times proportional to the authored scene lengths
total=sum(s['seconds'] for s in S)
ranges=[]
at=0
for s in S:
    end=at+duration*s['seconds']/total
    ranges.append((at,end,s))
    at=end
def pen(d,pts,color=aqua,w=20):
    d.line([(int(a),int(b)) for a,b in pts],fill=color,width=w,joint='curve')
def head(d,x,y,r=22):d.ellipse((int(x-r),int(y-r),int(x+r),int(y+r)),fill='#e7bc91')
def rep(t):
    q=(t%4.8)/4.8
    return (1-math.cos(2*math.pi*q))/2
def front(d,k):
    x=270; hy=490+110*k
    pen(d,[(x-34,hy),(190-18*k,625+25*k),(188,738)],aqua,25)
    pen(d,[(x+34,hy),(350+18*k,625+25*k),(352,738)],aqua,25)
    pen(d,[(170,741),(211,741)],fg,15)
    pen(d,[(333,741),(373,741)],fg,15)
    pen(d,[(x,hy),(x,hy-160)],fg,60)
    head(d,x,hy-210)
    pen(d,[(229,hy-142),(209,hy-86),(243,hy-34)],aqua,16)
    pen(d,[(312,hy-142),(334,hy-86),(295,hy-34)],aqua,16)
def side(d,k,cx=270):
    ankle=(cx+28,737);hip=(cx-25-49*k,470+135*k);L=136
    vx=ankle[0]-hip[0];vy=ankle[1]-hip[1]
    dist=max(.001,math.hypot(vx,vy))
    md=(dist/2)
    h=math.sqrt(max(0,L*L-md*md))
    knee=((hip[0]+ankle[0])/2+h*vy/dist,(hip[1]+ankle[1])/2-h*vx/dist)
    shoulder=(hip[0]+10+58*k,hip[1]-174+24*k)
    neck=(shoulder[0],shoulder[1]-27)
    pen(d,[hip,knee,ankle],aqua,25)
    pen(d,[ankle,(ankle[0]+61,ankle[1])],fg,16)
    pen(d,[hip,shoulder],fg,43)
    pen(d,[shoulder,(shoulder[0]+35,shoulder[1]+67),(shoulder[0]+70,shoulder[1]+93)],aqua,14)
    head(d,neck[0]+5,neck[1]-24)
def f(t):
    idx=next((i for i,(_,end,_) in enumerate(ranges) if t<end),len(S)-1)
    a,b,s=ranges[idx]
    im=Image.new('RGB',(W,H),bg)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((24,34,516,90),radius=22,fill='#14252b')
    d.text((45,52),'GYM LAB  /  TÉCNICA 01',font=ft(20,True),fill=aqua)
    d.text((28,124),s['title'],font=ft(35,True),fill=fg)
    d.text((28,185),s['caption'],font=ft(17,True),fill=aqua)
    d.rounded_rectangle((24,258,516,787),radius=30,fill='#14252b')
    pen(d,[(55,752),(485,752)],'#344e57',3)
    k=rep(t)
    if s['angle']=='front':front(d,k)
    else:side(d,k,245 if s['angle']=='side' else 267)
    d.text((270,824),'SIEMPRE CON CONTROL',anchor='mm',font=ft(21,True),fill=fg)
    d.rounded_rectangle((27,887,513,895),radius=4,fill='#334950')
    d.rounded_rectangle((27,887,27+max(1,int((486*t)/duration)),895),radius=4,fill=aqua)
    d.text((28,917),'ESPALDA ESTABLE  •  PIES FIRMES',font=ft(16),fill='#a3b2b5')
    return im
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i','out/voice.wav','-c:v','libx264','-preset','ultrafast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart','out/sentadilla-claude-code.mp4']
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(math.ceil(duration*FPS)):
    proc.stdin.write(f(i/FPS).tobytes())
proc.stdin.close()
if proc.wait()!=0:raise RuntimeError('Video encoder failed')
print('READY out/sentadilla-claude-code.mp4, seconds',duration)
