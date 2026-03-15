<script setup lang="ts">
import { onLaunch, onShow } from "@dcloudio/uni-app";

import { ensureAppSession } from "@/shared/services/auth";

// #ifdef H5
const PARTICLE_LAYER_ID = "xc-global-particles";
const TEXTURE_LAYER_ID = "xc-global-texture";

function ensureH5GlobalLayers() {
  if (typeof document === "undefined") {
    return;
  }

  if (!document.getElementById(PARTICLE_LAYER_ID)) {
    const particleLayer = document.createElement("div");
    particleLayer.id = PARTICLE_LAYER_ID;
    particleLayer.className = "xc-particle-layer";
    for (let index = 1; index <= 8; index += 1) {
      const particle = document.createElement("span");
      particle.className = `xc-particle xc-particle-${index}`;
      particleLayer.appendChild(particle);
    }
    document.body.appendChild(particleLayer);
  }

  let textureLayer = document.getElementById(TEXTURE_LAYER_ID) as HTMLDivElement | null;
  if (!textureLayer) {
    textureLayer = document.createElement("div");
    textureLayer.id = TEXTURE_LAYER_ID;
    textureLayer.className = "xc-texture-layer";
    document.body.appendChild(textureLayer);
  }
  textureLayer.innerHTML = `
    <svg width="100%" height="100%" style="position:absolute;inset:0;opacity:0.018;pointer-events:none">
      <filter id="xcNoise"><feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/></filter>
      <rect width="100%" height="100%" filter="url(#xcNoise)"/>
    </svg>
  `;
}
// #endif

onLaunch(() => {
  console.log("XinCe app launched");
  // #ifdef H5
  ensureH5GlobalLayers();
  // #endif
  ensureAppSession()
    .then(() => {
      // H5 should open the home/test flow directly. Redirecting during app launch
      // can leave the initial route blank before the router is fully ready.
    })
    .catch((error) => {
      console.warn("Failed to establish session on launch", error);
    });
});

onShow(() => {
  console.log("XinCe app visible");
  // #ifdef H5
  ensureH5GlobalLayers();
  // #endif
});
</script>

<style lang="scss">
page {
  background:
    radial-gradient(circle at top, rgba(155, 126, 216, 0.06), transparent 34%),
    radial-gradient(circle at 18% 14%, rgba(232, 114, 154, 0.04), transparent 40%),
    radial-gradient(circle at 82% 20%, rgba(124, 197, 178, 0.05), transparent 36%),
    linear-gradient(180deg, #fbf7f4 0%, #f5ede6 100%);
  color: $xc-ink;
  font-family: $xc-font-sans;
  position: relative;
}

page::after {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.015;
  background-image:
    repeating-linear-gradient(
      45deg,
      rgba(58, 46, 66, 0.8) 0,
      rgba(58, 46, 66, 0.8) 1px,
      transparent 1px,
      transparent 8px
    ),
    repeating-linear-gradient(
      -45deg,
      rgba(155, 126, 216, 0.8) 0,
      rgba(155, 126, 216, 0.8) 1px,
      transparent 1px,
      transparent 10px
    );
}

view,
text,
button {
  box-sizing: border-box;
  position: relative;
  z-index: 1;
}

.xc-particle-layer,
.xc-texture-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.xc-particle-layer {
  z-index: 0;
}

.xc-texture-layer {
  z-index: 0;
  opacity: 0.015;
  background-image:
    repeating-linear-gradient(
      0deg,
      rgba(58, 46, 66, 0.8) 0,
      rgba(58, 46, 66, 0.8) 1px,
      transparent 1px,
      transparent 9px
    ),
    repeating-linear-gradient(
      90deg,
      rgba(124, 93, 191, 0.6) 0,
      rgba(124, 93, 191, 0.6) 1px,
      transparent 1px,
      transparent 11px
    );
}

.xc-particle {
  position: fixed;
  bottom: -12vh;
  border-radius: 50%;
  opacity: 0;
  pointer-events: none;
  animation-name: floatUp;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
}

/* H5 scrollbar hiding must stay global. Scoped ::v-deep rules can compile into
 * a blanket [data-v-xxxx] selector that hides the whole page. */
/* #ifdef H5 */
::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}
/* #endif */

.xc-particle-1 {
  left: 7%;
  width: 3px;
  height: 3px;
  background: rgba(155, 126, 216, 0.34);
  animation-duration: 3.2s;
  animation-delay: 0.1s;
}

.xc-particle-2 {
  left: 18%;
  width: 5px;
  height: 5px;
  background: rgba(232, 114, 154, 0.24);
  animation-duration: 4.3s;
  animation-delay: 0.7s;
}

.xc-particle-3 {
  left: 31%;
  width: 4px;
  height: 4px;
  background: rgba(124, 197, 178, 0.25);
  animation-duration: 5.4s;
  animation-delay: 1.3s;
}

.xc-particle-4 {
  left: 44%;
  width: 6px;
  height: 6px;
  background: rgba(212, 168, 83, 0.22);
  animation-duration: 3.8s;
  animation-delay: 2.1s;
}

.xc-particle-5 {
  left: 58%;
  width: 3px;
  height: 3px;
  background: rgba(155, 126, 216, 0.24);
  animation-duration: 4.8s;
  animation-delay: 1.6s;
}

.xc-particle-6 {
  left: 69%;
  width: 4px;
  height: 4px;
  background: rgba(232, 114, 154, 0.26);
  animation-duration: 5.9s;
  animation-delay: 0.9s;
}

.xc-particle-7 {
  left: 82%;
  width: 5px;
  height: 5px;
  background: rgba(124, 197, 178, 0.23);
  animation-duration: 3.6s;
  animation-delay: 2.7s;
}

.xc-particle-8 {
  left: 92%;
  width: 6px;
  height: 6px;
  background: rgba(212, 168, 83, 0.2);
  animation-duration: 5.1s;
  animation-delay: 1.9s;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.88);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes popIn {
  from {
    opacity: 0;
    transform: scale(0.84);
  }

  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }

  100% {
    background-position: 200% 0;
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.05);
  }
}

@keyframes floatUp {
  0% {
    opacity: 0;
    transform: translateY(102vh) scale(0.25);
  }

  12% {
    opacity: 0.9;
  }

  90% {
    opacity: 0.45;
  }

  100% {
    opacity: 0;
    transform: translateY(-12vh) scale(1);
  }
}

@keyframes gentleBounce {
  0%,
  100% {
    transform: translateY(0);
  }

  35% {
    transform: translateY(-6px);
  }

  65% {
    transform: translateY(-2px);
  }
}

@keyframes glowPulse {
  0%,
  100% {
    box-shadow: 0 0 8px rgba(155, 126, 216, 0.2);
  }

  50% {
    box-shadow: 0 0 20px rgba(155, 126, 216, 0.4);
  }
}

@keyframes confettiPop {
  0% {
    opacity: 0;
    transform: translateY(0) scale(0.3) rotate(0deg);
  }

  20% {
    opacity: 1;
  }

  100% {
    opacity: 0;
    transform: translateY(-120px) scale(1) rotate(680deg);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes starPulse {
  0%,
  100% {
    opacity: 0.45;
    transform: scale(0.9);
  }

  50% {
    opacity: 1;
    transform: scale(1.12);
  }
}

@keyframes heartbeat {
  0%,
  100% {
    transform: scale(1);
  }

  15% {
    transform: scale(1.15);
  }

  30% {
    transform: scale(1);
  }

  45% {
    transform: scale(1.08);
  }
}

@keyframes sparkle {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(0.5);
  }

  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(40px);
  }

  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes countUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes revealSpin {
  0% {
    transform: rotateY(90deg);
    opacity: 0;
  }

  60% {
    transform: rotateY(-10deg);
    opacity: 1;
  }

  100% {
    transform: rotateY(0deg);
    opacity: 1;
  }
}

@keyframes glow {
  0%,
  100% {
    box-shadow: 0 0 8px rgba(155, 126, 216, 0.2);
  }

  50% {
    box-shadow: 0 0 20px rgba(155, 126, 216, 0.4);
  }
}

@keyframes rainbow {
  0% {
    border-color: rgba(201, 181, 240, 0.85);
  }

  25% {
    border-color: rgba(244, 165, 191, 0.85);
  }

  50% {
    border-color: rgba(242, 166, 139, 0.85);
  }

  75% {
    border-color: rgba(168, 221, 208, 0.85);
  }

  100% {
    border-color: rgba(201, 181, 240, 0.85);
  }
}

@keyframes hiddenShake {
  0%,
  100% {
    transform: translateX(0);
  }

  10%,
  30%,
  50%,
  70%,
  90% {
    transform: translateX(-1px);
  }

  20%,
  40%,
  60%,
  80% {
    transform: translateX(1px);
  }
}

/* --- Global utility classes --- */

.xc-anim-fu {
  animation: fadeInUp 0.5s $xc-ease both;
}

.xc-anim-si {
  animation: scaleIn 0.45s $xc-ease both;
}

.xc-anim-sl {
  animation: slideIn 0.5s $xc-ease both;
}

.xc-anim-pi {
  animation: popIn 0.4s $xc-spring both;
}

.xc-d1 {
  animation-delay: 0.06s;
}

.xc-d2 {
  animation-delay: 0.12s;
}

.xc-d3 {
  animation-delay: 0.18s;
}

.xc-d4 {
  animation-delay: 0.24s;
}

.xc-d5 {
  animation-delay: 0.3s;
}
</style>
