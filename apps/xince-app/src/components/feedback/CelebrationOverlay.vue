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
    left: `${12 + (index % 4) * 20}%`,
    delay: `${index * 0.06}s`,
    duration: `${1.2 + (index % 3) * 0.18}s`,
    travelX: `${-120 + index * 22}rpx`,
    color: ["#ff8b6b", "#ffc86b", "#8ad7a1", "#86b6ff"][index % 4],
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
  SoundManager.haptic(60);
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
        }"
      />
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
  background: rgba(32, 20, 16, 0.62);
  backdrop-filter: blur(10px);
}

.celebration__panel {
  position: relative;
  width: 100%;
  max-width: 620rpx;
  padding: 56rpx 40rpx 42rpx;
  border-radius: 36rpx;
  background: linear-gradient(180deg, rgba(255, 249, 240, 0.98), rgba(255, 237, 216, 0.94));
  box-shadow: 0 24rpx 80rpx rgba(91, 46, 21, 0.18);
  overflow: hidden;
  animation: celebration-pop 0.36s ease-out;
}

.celebration__particle {
  position: absolute;
  top: 32%;
  width: 16rpx;
  height: 34rpx;
  border-radius: 999rpx;
  opacity: 0;
  animation-name: confetti-pop;
  animation-fill-mode: both;
  animation-timing-function: ease-out;
}

.celebration__title {
  display: block;
  text-align: center;
  font-size: 38rpx;
  font-weight: 700;
  color: #7b3c1e;
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
}

.celebration__name {
  margin-top: 14rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: #2b2118;
}

.celebration__message {
  display: block;
  margin-top: 20rpx;
  text-align: center;
  font-size: 26rpx;
  line-height: 1.7;
  color: rgba(43, 33, 24, 0.76);
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
    transform: scale(0.82);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes confetti-pop {
  0% {
    opacity: 0;
    transform: translate3d(0, 0, 0) rotate(0deg) scale(0.5);
  }
  20% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translate3d(var(--travel-x), -220rpx, 0) rotate(220deg) scale(1);
  }
}
</style>
