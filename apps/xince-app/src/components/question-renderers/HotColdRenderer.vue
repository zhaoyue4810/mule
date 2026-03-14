<script setup lang="ts">
import { computed, getCurrentInstance, ref } from "vue";

import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: number | null;
  labels?: string[];
  emojis?: string[];
  minLabel?: string;
  maxLabel?: string;
  min?: number;
  max?: number;
  step?: number;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const proxy = getCurrentInstance()?.proxy;
const flash = ref(false);
const tubeRect = ref<UniApp.NodeInfo | null>(null);
const current = computed(() => props.modelValue ?? props.min ?? 1);
const progress = computed(() => ((current.value - (props.min ?? 1)) / Math.max(1, (props.max ?? 5) - (props.min ?? 1))));
const tempEmoji = computed(() => {
  if (progress.value > 0.75) return "🔥";
  if (progress.value > 0.45) return "😐";
  return "❄️";
});

async function ensureRect() {
  if (tubeRect.value) return tubeRect.value;
  return new Promise<UniApp.NodeInfo | null>((resolve) => {
    if (!proxy) {
      resolve(null);
      return;
    }
    uni.createSelectorQuery()
      .in(proxy)
      .select(".hotcold__tube")
      .boundingClientRect((rect) => {
        const parsed = Array.isArray(rect) ? rect[0] : rect;
        tubeRect.value = parsed || null;
        resolve(tubeRect.value);
      })
      .exec();
  });
}

async function updateByTouch(event: { touches?: Array<{ clientY?: number; pageY?: number }> }) {
  const touch = event.touches?.[0];
  if (!touch) return;
  const rect = await ensureRect();
  if (!rect || !rect.height || !rect.top) return;
  const y = touch.clientY ?? touch.pageY ?? rect.top;
  const ratio = 1 - Math.min(1, Math.max(0, (y - rect.top) / rect.height));
  const min = props.min ?? 1;
  const max = props.max ?? 5;
  const raw = min + ratio * (max - min);
  const step = props.step ?? 1;
  const snapped = Math.round(raw / step) * step;
  emit("update:modelValue", Math.min(max, Math.max(min, snapped)));
}

function confirm() {
  playSound("chime");
  haptic(15);
  flash.value = true;
  setTimeout(() => (flash.value = false), 300);
}
</script>

<template>
  <view class="hotcold q-enter">
    <view v-if="flash" class="edge-flash" />
    <text class="hotcold__label">{{ maxLabel || "热" }}</text>
    <view
      class="hotcold__tube"
      @touchstart.stop.prevent="updateByTouch"
      @touchmove.stop.prevent="updateByTouch"
      @touchend.stop.prevent="confirm"
    >
      <view class="hotcold__fill" :style="{ height: `${progress * 100}%` }" />
    </view>
    <text class="hotcold__label">{{ minLabel || "冷" }}</text>
    <text class="hotcold__emoji">{{ tempEmoji }}</text>
  </view>
</template>

<style lang="scss" scoped>
.hotcold {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.hotcold__tube {
  width: 92rpx;
  height: 360rpx;
  border-radius: 999rpx;
  background: linear-gradient(180deg, #ff7a6d, #f8f8f8 52%, #6aa5ff);
  border: 2rpx solid rgba(155, 126, 216, 0.14);
  overflow: hidden;
  display: flex;
  align-items: flex-end;
}

.hotcold__fill {
  width: 100%;
  background: linear-gradient(180deg, #ff6a59, #ffffff 55%, #4a83ff);
  transition: height 0.15s ease;
}

.hotcold__emoji {
  font-size: 34rpx;
}

.hotcold__label {
  color: $xc-muted;
  font-size: 22rpx;
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

@keyframes edgeFlash {
  from {
    box-shadow: inset 0 0 0 0 rgba(255, 106, 89, 0.5);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(74, 131, 255, 0);
  }
}
</style>
