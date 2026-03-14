<script setup lang="ts">
import { computed, ref } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { SoundManager } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

function choose(value: string) {
  SoundManager.play("ambient");
  SoundManager.haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  emit("update:modelValue", value);
}
const flash = ref(false);

const fallbackPositions = [
  { x: 14, y: 28 },
  { x: 62, y: 12 },
  { x: 36, y: 58 },
  { x: 78, y: 48 },
  { x: 18, y: 78 },
];

function normalizePercent(value: unknown, fallback: number): number {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      return fallback;
    }
    if (value >= 0 && value <= 1) {
      return value * 100;
    }
    return Math.min(100, Math.max(0, value));
  }
  if (typeof value === "string") {
    const raw = value.trim();
    const parsed = Number(raw.replace("%", ""));
    if (!Number.isFinite(parsed)) {
      return fallback;
    }
    if (raw.endsWith("%")) {
      return Math.min(100, Math.max(0, parsed));
    }
    if (parsed >= 0 && parsed <= 1) {
      return parsed * 100;
    }
    return Math.min(100, Math.max(0, parsed));
  }
  return fallback;
}

const starPoints = computed(() => {
  const config = (props.question.config || {}) as Record<string, unknown>;
  const configured = Array.isArray(config.positions) ? config.positions : [];
  return props.question.options.map((option, index) => {
    const fallback = fallbackPositions[index % fallbackPositions.length];
    const point = configured[index] as Record<string, unknown> | undefined;
    const x = normalizePercent(point?.x, fallback.x);
    const y = normalizePercent(point?.y, fallback.y);
    return {
      optionCode: option.option_code || String(option.seq),
      label: option.label,
      emoji: option.emoji || "✦",
      left: `${x}%`,
      top: `${y}%`,
      x,
      y,
    };
  });
});

const lineSegments = computed(() => {
  const points = starPoints.value;
  return points.slice(1).map((point, index) => {
    const prev = points[index];
    const dx = point.x - prev.x;
    const dy = point.y - prev.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx);
    return {
      left: `${prev.x}%`,
      top: `${prev.y}%`,
      width: `${length}%`,
      transform: `rotate(${angle}rad)`,
      animationDelay: `${index * 60}ms`,
    };
  });
});
</script>

<template>
  <view class="constellation q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="constellation__board">
      <view
        v-for="(line, index) in lineSegments"
        :key="`line-${index}`"
        class="constellation__line"
        :style="line"
      />
      <view
        v-for="point in starPoints"
        :key="point.optionCode"
        class="constellation__star"
        :class="{ 'constellation__star--active': modelValue === point.optionCode }"
        :style="{ left: point.left, top: point.top }"
        @tap="choose(point.optionCode)"
      >
        <text class="constellation__glyph">{{ point.emoji }}</text>
        <text class="constellation__label">{{ point.label }}</text>
      </view>
    </view>
    <text class="constellation__tip">点亮最像你此刻轨迹的那颗星。</text>
  </view>
</template>

<style lang="scss" scoped>
.constellation {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.constellation__board {
  position: relative;
  min-height: 420rpx;
  border-radius: 28rpx;
  background:
    radial-gradient(circle at top, rgba(131, 109, 199, 0.18), rgba(34, 27, 56, 0.92)),
    #241c3f;
  overflow: hidden;
}

.constellation__board::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.8) 0, transparent 8rpx),
    radial-gradient(circle at 70% 28%, rgba(255, 255, 255, 0.7) 0, transparent 6rpx),
    radial-gradient(circle at 46% 74%, rgba(255, 255, 255, 0.6) 0, transparent 7rpx);
  opacity: 0.35;
  pointer-events: none;
  animation: constTwinkle 2.8s ease-in-out infinite;
}

.constellation__line {
  position: absolute;
  height: 2rpx;
  margin-left: 0;
  margin-top: 0;
  transform-origin: left center;
  background: linear-gradient(
    to right,
    rgba(255, 255, 255, 0.65),
    rgba(255, 223, 196, 0.45)
  );
  pointer-events: none;
  z-index: 1;
  animation: lineFade 0.45s ease both;
}

.constellation__star {
  position: absolute;
  width: 132rpx;
  min-height: 108rpx;
  padding: 18rpx 10rpx;
  margin-left: -66rpx;
  margin-top: -54rpx;
  border-radius: 22rpx;
  text-align: center;
  background: rgba(255, 255, 255, 0.12);
  border: 2rpx solid rgba(255, 255, 255, 0.2);
  color: #fffaf3;
  backdrop-filter: blur(8rpx);
  z-index: 2;
}

.constellation__star--active {
  background: rgba(255, 223, 196, 0.26);
  border-color: rgba(255, 227, 200, 0.78);
  box-shadow: 0 0 22rpx rgba(255, 212, 179, 0.45);
  transform: scale(1.08);
}

.constellation__glyph {
  display: block;
  font-size: 30rpx;
}

.constellation__label {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.5;
}

.constellation__tip {
  font-size: 22rpx;
  color: $xc-muted;
}

.edge-flash {
  position: absolute;
  inset: 0;
  animation: edgeFlash 0.3s ease;
}

.q-enter {
  animation: qEnter 0.4s $xc-ease both;
}

@keyframes qEnter {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes constTwinkle {
  0%,
  100% {
    opacity: 0.22;
  }
  50% {
    opacity: 0.45;
  }
}

@keyframes lineFade {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes edgeFlash {
  from {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.55);
  }
  to {
    box-shadow: inset 0 0 0 16rpx rgba(155, 126, 216, 0);
  }
}
</style>
