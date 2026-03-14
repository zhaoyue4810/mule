<script setup lang="ts">
import { computed, getCurrentInstance, ref } from "vue";

import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: number | null;
  hueMap?: Record<string, unknown>;
  minHue?: number;
  maxHue?: number;
  step?: number;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const proxy = getCurrentInstance()?.proxy;
const rect = ref<UniApp.NodeInfo | null>(null);
const currentHue = ref(props.modelValue ?? 0);
const flash = ref(false);
let confirmTimer: ReturnType<typeof setTimeout> | null = null;

const pointerStyle = computed(() => {
  const rad = (currentHue.value / 180) * Math.PI;
  const r = 86;
  const x = 100 + Math.cos(rad) * r;
  const y = 100 + Math.sin(rad) * r;
  return { left: `${x}rpx`, top: `${y}rpx` };
});
const mood = computed(() => {
  const hue = currentHue.value;
  if (hue < 50) return "热情";
  if (hue < 95) return "乐观";
  if (hue < 170) return "平和";
  if (hue < 250) return "忧郁";
  return "神秘";
});

async function ensureRect() {
  if (rect.value) return rect.value;
  return new Promise<UniApp.NodeInfo | null>((resolve) => {
    if (!proxy) return resolve(null);
    uni.createSelectorQuery()
      .in(proxy)
      .select(".cpick__wheel")
      .boundingClientRect((r) => {
        rect.value = (Array.isArray(r) ? r[0] : r) || null;
        resolve(rect.value);
      })
      .exec();
  });
}

async function pick(event: { touches?: Array<{ clientX?: number; pageX?: number; clientY?: number; pageY?: number }> }) {
  const touch = event.touches?.[0];
  if (!touch) return;
  const box = await ensureRect();
  if (!box || !box.width || !box.height || box.left == null || box.top == null) return;
  const x = (touch.clientX ?? touch.pageX ?? box.left) - (box.left + box.width / 2);
  const y = (touch.clientY ?? touch.pageY ?? box.top) - (box.top + box.height / 2);
  let hue = (Math.atan2(y, x) * 180) / Math.PI;
  if (hue < 0) hue += 360;
  const min = props.minHue ?? 0;
  const max = props.maxHue ?? 360;
  const step = props.step ?? 1;
  const snapped = Math.round(hue / step) * step;
  currentHue.value = Math.min(max, Math.max(min, snapped));
  if (confirmTimer) clearTimeout(confirmTimer);
  confirmTimer = setTimeout(() => {
    emit("update:modelValue", currentHue.value);
    playSound("chime");
    haptic(15);
    flash.value = true;
    setTimeout(() => (flash.value = false), 300);
  }, 800);
}
</script>

<template>
  <view class="cpick q-enter">
    <view v-if="flash" class="edge-flash" />
    <view
      class="cpick__wheel"
      @touchstart.stop.prevent="pick"
      @touchmove.stop.prevent="pick"
    >
      <view class="cpick__pointer" :style="pointerStyle" />
    </view>
    <text class="cpick__label">{{ currentHue }}° · {{ mood }}</text>
  </view>
</template>

<style lang="scss" scoped>
.cpick {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.cpick__wheel {
  width: 200rpx;
  height: 200rpx;
  border-radius: 50%;
  background: conic-gradient(red, yellow, lime, cyan, blue, magenta, red);
  position: relative;
}

.cpick__pointer {
  position: absolute;
  width: 18rpx;
  height: 18rpx;
  margin-left: -9rpx;
  margin-top: -9rpx;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 4rpx rgba(58, 46, 66, 0.18);
}

.cpick__label {
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

@keyframes edgeFlash {
  from {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.55);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>
