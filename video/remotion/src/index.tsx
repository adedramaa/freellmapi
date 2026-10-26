import React from 'react';
import {ZombieEpisode} from './ZombieEpisode';
import {AbsoluteFill, Composition, interpolate, registerRoot, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type Scene = {heading: string; caption: string};
type VideoProps = {
  title: string;
  subtitle: string;
  background: string;
  accent: string;
  scenes: Scene[];
};

const defaults: VideoProps = {
  title: 'REMOTION',
  subtitle: 'Videos creados desde el chat',
  background: '#0b1020',
  accent: '#76e8c7',
  scenes: [{heading: 'CREAR', caption: 'Diseñar cuadro por cuadro'}, {heading: 'ANIMAR', caption: 'Movimiento y continuidad'}, {heading: 'EXPORTAR', caption: 'Tu video MP4'}],
};

const CloudVideo: React.FC<VideoProps> = ({title, subtitle, background, accent, scenes}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames, width, height} = useVideoConfig();
  const safeScenes = scenes.length ? scenes : defaults.scenes;
  const framesPerScene = Math.max(1, durationInFrames / safeScenes.length);
  const idx = Math.min(safeScenes.length - 1, Math.floor(frame / framesPerScene));
  const local = frame - idx * framesPerScene;
  const active = safeScenes[idx];
  const entrance = spring({frame: local, fps, config: {damping: 180, stiffness: 85, mass: 1}});
  const fadeOut = interpolate(local, [framesPerScene - 16, framesPerScene], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const progress = frame / Math.max(1, durationInFrames - 1);
  const scale = 1 + 0.03 * Math.sin(frame / 18);
  const orbX = Math.sin(frame / 43) * width * .18;
  const orbY = Math.cos(frame / 49) * height * .08;

  return (
    <AbsoluteFill style={{background, color: '#fff', fontFamily: 'Arial, Helvetica, sans-serif', overflow: 'hidden'}}>
      <AbsoluteFill style={{background: `radial-gradient(ellipse at 55% 33%, ${accent}22, transparent 64%), linear-gradient(145deg, transparent 30%, #03050e88 100%)`}} />
      <div style={{position: 'absolute', width: width * .92, height: width * .92, borderRadius: '50%', left: width * .25 + orbX, top: height * .12 + orbY, background: accent, filter: 'blur(120px)', opacity: .22, transform: `scale(${scale})`}} />
      <div style={{position: 'absolute', left: width * .07, top: height * .095, fontWeight: 800, letterSpacing: 6, fontSize: width * .033, opacity: .85}}>{title.toUpperCase()}</div>
      <div style={{position: 'absolute', right: width * .07, top: height * .097, fontSize: width * .025, fontWeight: 600, letterSpacing: 4, opacity: .55}}>{String(idx + 1).padStart(2, '0')} / {String(safeScenes.length).padStart(2, '0')}</div>
      <div style={{position: 'absolute', left: width * .08, top: height * .3, width: width * .84, transform: `translateY(${(1 - entrance) * 90}px)`, opacity: entrance * fadeOut}}>
        <div style={{height: 9, width: 86, background: accent, borderRadius: 12, marginBottom: 49}} />
        <div style={{fontSize: width * (active.heading.length > 14 ? .084 : .118), fontWeight: 900, letterSpacing: -4, lineHeight: 1.03, overflowWrap: 'anywhere', textShadow: '0px 9px 30px #0005'}}>{active.heading}</div>
        <div style={{fontSize: width * .046, marginTop: 43, fontWeight: 500, lineHeight: 1.38, color: '#dce8f1', overflowWrap: 'anywhere'}}>{active.caption}</div>
      </div>
      <div style={{position: 'absolute', left: width * .08, right: width * .08, bottom: height * .14, fontSize: width * .035, fontWeight: 500, color: '#a8b9c9', lineHeight: 1.35}}>{subtitle}</div>
      <div style={{position: 'absolute', left: width * .08, bottom: height * .088, width: width * .84, height: 8, background: '#ffffff22', borderRadius: 5, overflow: 'hidden'}}>
        <div style={{width: `${progress * 100}%`, height: '100%', borderRadius: 5, background: accent}} />
      </div>
    </AbsoluteFill>
  );
};

const Root = () => (
  <>
    <Composition id="CloudVideo" component={CloudVideo} width={720} height={1280} fps={30} durationInFrames={360} defaultProps={defaults} />
    <Composition id="ZombieEpisode" component={ZombieEpisode} width={720} height={1280} fps={30} durationInFrames={1200} defaultProps={{...defaults,kind:'zombie-episode-1',hasVoice:false}} />
  </>
);

registerRoot(Root);
