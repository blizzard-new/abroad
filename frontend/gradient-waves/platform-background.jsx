import { Component } from 'react';
import { createRoot } from 'react-dom/client';
import GradientWaves from './GradientWaves';
import './platform-background.css';

// Keep the registry component intact; platform behavior lives in this adapter.
class BackgroundBoundary extends Component {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch() {
    this.props.host.dataset.state = 'fallback';
  }

  render() {
    return this.state.failed ? null : this.props.children;
  }
}

const host = document.getElementById('platform-background');

if (host) {
  const root = createRoot(host);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const render = () => {
    host.dataset.state = reducedMotion.matches ? 'reduced-motion' : 'animated';
    root.render(
      <BackgroundBoundary host={host}>
        {reducedMotion.matches ? null : (
          <GradientWaves
            horizonColor="#14cdd8"
            waveColor="#4264cc"
            crestColor="#FFFFFF"
            speed={0.4}
            amplitude={2.5}
            waveScale={0.6}
            waveRatio={0.9}
            swell={35}
            turbulence={20}
            tilt={1.11}
            zoom={1.0}
            height={5.5}
            fogDepth={15}
            detail="medium"
            brightness={1.0}
            opacity={1.0}
            mouseInteraction={true}
            parallaxStrength={0.5}
            grain={true}
            grainIntensity={0.05}
          />
        )}
      </BackgroundBoundary>
    );
  };

  // Forward pointer coordinates to the registry's canvas without covering links,
  // forms, maps or dialogs with a pointer target.
  const forwardPointer = event => {
    if (event.pointerType !== 'mouse') return;
    host.querySelector('canvas')?.dispatchEvent(new PointerEvent('pointermove', {
      clientX: event.clientX,
      clientY: event.clientY,
    }));
  };
  const resetPointer = () => {
    host.querySelector('canvas')?.dispatchEvent(new PointerEvent('pointerleave'));
  };

  // WebGL context loss falls back to the same static ocean palette.
  host.addEventListener('webglcontextlost', () => {
    host.dataset.state = 'fallback';
    root.render(null);
  }, true);
  reducedMotion.addEventListener('change', render);
  window.addEventListener('pointermove', forwardPointer, { passive: true });
  document.documentElement.addEventListener('pointerleave', resetPointer);
  render();
}
