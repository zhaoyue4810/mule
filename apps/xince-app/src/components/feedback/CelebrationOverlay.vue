<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from "vue";

import { SoundManager } from "@/shared/utils/sound-manager";

interface CelebrationBadgeItem {
  badge_key: string;
  name: string;
  emoji: string;
  tier?: number;
}

const props = withDefaults(
  defineProps<{
    visible: boolean;
    title?: string;
    message?: string;
    badges?: CelebrationBadgeItem[];
  }>(),
  {
    title: "太棒了！",
    message: "新的成长印记已经点亮。",
    badges: () => [],
  },
);

const emit = defineEmits<{
  close: [];
}>();

let closeTimer: ReturnType<typeof setTimeout> | null = null;

const particles = computed(() =>
  Array.from({ length: 12 }, (_, index) => ({
    id: index,
    left: "50%",
    delay: `${index * 0.04}s`,
    duration: "1s",
    travelX: `${Math.cos((Math.PI * 2 * index) / 12) * (120 + (index % 3) * 24)}rpx`,
    travelY: `${-120 - Math.sin((Math.PI * 2 * index) / 12) * (90 + (index % 4) * 22)}rpx`,
    rotate: `${index % 2 === 0 ? 260 : -260}deg`,
    color: ["#9B7ED8", "#E8729A", "#7CC5B2", "#D4A853", "#F2A68B"][index % 5],
    size: `${6 + (index % 4) * 2}rpx`,
  })),
);

const featuredBadge = computed(() => props.badges[0] || null);

function clearCloseTimer() {
  if (closeTimer) {
    clearTimeout(closeTimer);
    closeTimer = null;
  }
}

function closeOverlay() {
  clearCloseTimer();
  emit("close");
}

function playCelebrationFeedback() {
  SoundManager.haptic(30);
  SoundManager.play("chime");
}

watch(
  () => props.visible,
  (visible) => {
    clearCloseTimer();
    if (!visible) {
      return;
    }
    playCelebrationFeedback();
    closeTimer = setTimeout(() => {
      emit("close");
    }, 3000);
  },
);

onBeforeUnmount(() => {
  clearCloseTimer();
});
</script>

<template>
  <view v-if="visible" class="celebration" @tap="closeOverlay">
    <view class="celebration__mask" />
    <view class="celebration__panel" @tap.stop>
      <view
        v-for="particle in particles"
        :key="particle.id"
        class="celebration__particle"
        :style="{
          left: particle.left,
          animationDelay: particle.delay,
          animationDuration: particle.duration,
          background: particle.color,
          '--travel-x': particle.travelX,
          '--travel-y': particle.travelY,
          '--rotate': particle.rotate,
          width: particle.size,
          height: particle.size,
        }"
      />
      <text class="celebration__wow">太棒了!</text>
      <text class="celebration__title">{{ title }}</text>
      <view v-if="featuredBadge" class="celebration__badge">
        <text class="celebration__emoji">{{ featuredBadge.emoji }}</text>
        <text class="celebration__name">{{ featuredBadge.name }}</text>
      </view>
      <text class="celebration__message">{{ message }}</text>
      <view v-if="badges.length > 1" class="celebration__list">
        <text
          v-for="item in badges.slice(1)"
          :key="item.badge_key"
          class="celebration__list-item"
        >
          {{ item.emoji }} {{ item.name }}
        </text>
      </view>
      <text class="celebration__hint">轻点任意位置关闭</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.celebration {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}

.celebration__mask {
  position: absolute;
  inset: 0;
  background: rgba(42, 28, 58, 0.72);
  backdrop-filter: blur(10px);
}

.celebration__panel {
  position: relative;
  width: 100%;
  max-width: 620rpx;
  padding: 56rpx 40rpx 42rpx;
  border-radius: 36rpx;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(237, 229, 249, 0.92));
  box-shadow: 0 24rpx 80rpx rgba(58, 46, 66, 0.26);
  overflow: hidden;
  animation: celebration-pop 0.36s $xc-spring;
}

.celebration__particle {
  position: absolute;
  top: 52%;
  border-radius: 2rpx;
  opacity: 0;
  animation-name: confetti-pop;
  animation-fill-mode: both;
  animation-timing-function: ease-out;
}

.celebration__wow {
  display: block;
  text-align: center;
  font-size: 44rpx;
  font-weight: 700;
  color: $xc-purple;
  text-shadow: 0 0 16rpx rgba(155, 126, 216, 0.45);
  animation: fadeInUp 0.3s $xc-ease both;
}

.celebration__title {
  display: block;
  text-align: center;
  margin-top: 10rpx;
  font-size: 38rpx;
  font-weight: 700;
  color: #3A2E42;
  animation: fadeInUp 0.4s $xc-ease both;
}

.celebration__badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 24rpx;
}

.celebration__emoji {
  font-size: 84rpx;
  line-height: 1;
  animation: badge-pop 0.34s $xc-spring both;
}

.celebration__name {
  margin-top: 14rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: #3A2E42;
}

.celebration__message {
  display: block;
  margin-top: 20rpx;
  text-align: center;
  font-size: 26rpx;
  line-height: 1.7;
  color: rgba(58, 46, 66, 0.76);
  animation: fadeInUp 0.46s $xc-ease both;
}

.celebration__list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12rpx;
  margin-top: 20rpx;
}

.celebration__list-item {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  font-size: 22rpx;
  color: #6d4b38;
}

.celebration__hint {
  display: block;
  margin-top: 22rpx;
  text-align: center;
  font-size: 22rpx;
  color: rgba(123, 60, 30, 0.62);
}

@keyframes celebration-pop {
  from {
    opacity: 0;
    transform: scale(0);
  }
  70% {
    opacity: 1;
    transform: scale(1.2);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes badge-pop {
  0% {
    transform: scale(0);
  }
  70% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes confetti-pop {
  0% {
    opacity: 0;
    transform: translate3d(0, 0, 0) rotate(0deg) scale(0.6);
  }
  20% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translate3d(var(--travel-x), var(--travel-y), 0) rotate(var(--rotate)) scale(1);
  }
}
</style>
