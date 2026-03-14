<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from "vue";

import type { TimeCapsuleItem } from "@/shared/models/capsule";
import { SoundManager } from "@/shared/utils/sound-manager";

const props = defineProps<{
  visible: boolean;
  item: TimeCapsuleItem | null;
}>();

const emit = defineEmits<{
  close: [];
}>();

let timer: ReturnType<typeof setTimeout> | null = null;

const particles = computed(() =>
  Array.from({ length: 12 }, (_, index) => ({
    id: index,
    left: `${16 + (index % 4) * 18}%`,
    delay: `${index * 0.05}s`,
    color: ["#f5b75b", "#f18f63", "#f2d28a", "#fff4cd"][index % 4],
    travelX: `${-110 + index * 20}rpx`,
  })),
);

function clearTimer() {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
}

function closeReveal() {
  clearTimer();
  emit("close");
}

watch(
  () => props.visible,
  (visible) => {
    clearTimer();
    if (!visible) {
      return;
    }
    SoundManager.play("chime");
    SoundManager.haptic(80);
    timer = setTimeout(() => {
      emit("close");
    }, 5000);
  },
);

onBeforeUnmount(() => {
  clearTimer();
});
</script>

<template>
  <view v-if="visible && item" class="reveal" @tap="closeReveal">
    <view class="reveal__mask" />
    <view class="reveal__panel" @tap.stop>
      <view
        v-for="particle in particles"
        :key="particle.id"
        class="reveal__particle"
        :style="{
          left: particle.left,
          animationDelay: particle.delay,
          background: particle.color,
          '--travel-x': particle.travelX,
        }"
      />
      <text class="reveal__eyebrow">来自过去的你</text>
      <text class="reveal__icon">{{ item.persona_icon || "💌" }}</text>
      <text class="reveal__title">{{ item.persona_title || "时光胶囊" }}</text>
      <text class="reveal__body">{{ item.message }}</text>
      <text class="reveal__hint">轻点任意位置收起</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.reveal {
  position: fixed;
  inset: 0;
  z-index: 95;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

.reveal__mask {
  position: absolute;
  inset: 0;
  background: rgba(23, 15, 10, 0.76);
  backdrop-filter: blur(10px);
}

.reveal__panel {
  position: relative;
  width: 100%;
  max-width: 640rpx;
  padding: 60rpx 42rpx 46rpx;
  border-radius: 36rpx;
  background: linear-gradient(180deg, #fff3d7, #f8ddb4);
  box-shadow: 0 32rpx 96rpx rgba(0, 0, 0, 0.28);
  overflow: hidden;
  animation: reveal-rise 0.36s ease-out;
}

.reveal__particle {
  position: absolute;
  top: 28%;
  width: 14rpx;
  height: 30rpx;
  border-radius: 999rpx;
  opacity: 0;
  animation: reveal-confetti 1.2s ease-out both;
}

.reveal__eyebrow,
.reveal__hint {
  display: block;
  text-align: center;
  color: rgba(79, 55, 31, 0.72);
}

.reveal__eyebrow {
  font-size: 24rpx;
  letter-spacing: 4rpx;
}

.reveal__icon {
  display: block;
  margin-top: 22rpx;
  text-align: center;
  font-size: 84rpx;
}

.reveal__title {
  display: block;
  margin-top: 14rpx;
  text-align: center;
  font-size: 36rpx;
  font-weight: 700;
  color: #4a321b;
}

.reveal__body {
  display: block;
  margin-top: 24rpx;
  font-size: 28rpx;
  line-height: 1.9;
  color: #5b432d;
  text-align: center;
}

.reveal__hint {
  margin-top: 28rpx;
  font-size: 22rpx;
}

@keyframes reveal-rise {
  from {
    opacity: 0;
    transform: translateY(40rpx) scale(0.92);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes reveal-confetti {
  0% {
    opacity: 0;
    transform: translate3d(0, 0, 0) scale(0.5);
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
