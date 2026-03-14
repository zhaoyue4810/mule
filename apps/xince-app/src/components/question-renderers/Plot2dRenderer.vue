<script setup lang="ts">
import { computed, getCurrentInstance, ref } from "vue";

import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: { x: number; y: number } | null;
  xMin?: string;
  xMax?: string;
  yMin?: string;
  yMax?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: { x: number; y: number }];
}>();

const proxy = getCurrentInstance()?.proxy;
const boardRect = ref<UniApp.NodeInfo | null>(null);
const dragging = ref(false);
const flash = ref(false);
const point = computed(() => props.modelValue || { x: 0.5, y: 0.5 });

async function ensureRect() {
  if (boardRect.value) return boardRect.value;
  return new Promise<UniApp.NodeInfo | null>((resolve) => {
    if (!proxy) {
      resolve(null);
      return;
    }
    uni.createSelectorQuery()
      .in(proxy)
      .select(".plot__board")
      .boundingClientRect((rect) => {
        boardRect.value = (Array.isArray(rect) ? rect[0] : rect) || null;
        resolve(boardRect.value);
      })
      .exec();
  });
}

async function updateByTouch(event: { touches?: Array<{ clientX?: number; pageX?: number; clientY?: number; pageY?: number }> }) {
  const touch = event.touches?.[0];
  if (!touch) return;
  const rect = await ensureRect();
  if (!rect || !rect.width || !rect.height || rect.left == null || rect.top == null) return;
  const x = (touch.clientX ?? touch.pageX ?? rect.left) - rect.left;
  const y = (touch.clientY ?? touch.pageY ?? rect.top) - rect.top;
  const nx = Math.min(1, Math.max(0, x / rect.width));
  const ny = Math.min(1, Math.max(0, 1 - y / rect.height));
  emit("update:modelValue", { x: Number(nx.toFixed(3)), y: Number(ny.toFixed(3)) });
}

function onStart(event: { touches?: Array<{ clientX?: number; pageX?: number; clientY?: number; pageY?: number }> }) {
  dragging.value = true;
  void updateByTouch(event);
}

function onMove(event: { touches?: Array<{ clientX?: number; pageX?: number; clientY?: number; pageY?: number }> }) {
  if (!dragging.value) return;
  void updateByTouch(event);
}

function onEnd() {
  dragging.value = false;
  playSound("chime");
  haptic(15);
  flash.value = true;
  setTimeout(() => (flash.value = false), 300);
}
</script>

<template>
  <view class="plot q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="plot__axis plot__axis--top">
      <text>{{ yMax || "理性" }}</text>
      <text>{{ xMax || "外向" }}</text>
    </view>
    <view
      class="plot__board"
      @touchstart.stop.prevent="onStart"
      @touchmove.stop.prevent="onMove"
      @touchend.stop.prevent="onEnd"
      @touchcancel.stop.prevent="onEnd"
    >
      <view class="plot__cross plot__cross--x" :style="{ left: `${point.x * 100}%` }" />
      <view class="plot__cross plot__cross--y" :style="{ top: `${(1 - point.y) * 100}%` }" />
      <view class="plot__dot" :style="{ left: `${point.x * 100}%`, top: `${(1 - point.y) * 100}%` }" />
    </view>
    <view class="plot__axis">
      <text>{{ yMin || "感性" }}</text>
      <text>{{ xMin || "内向" }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.plot {
  position: relative;
}

.plot__axis {
  display: flex;
  justify-content: space-between;
  color: $xc-muted;
  font-size: 22rpx;
}

.plot__axis--top {
  margin-bottom: 8rpx;
}

.plot__board {
  width: 240rpx;
  height: 240rpx;
  margin: 0 auto;
  position: relative;
  border-radius: 18rpx;
  background:
    linear-gradient(to right, transparent 49.5%, rgba(155, 126, 216, 0.12) 50%, transparent 50.5%),
    linear-gradient(to top, transparent 49.5%, rgba(155, 126, 216, 0.12) 50%, transparent 50.5%),
    rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(155, 126, 216, 0.2);
}

.plot__cross {
  position: absolute;
  background: rgba(155, 126, 216, 0.24);
}

.plot__cross--x {
  top: 0;
  bottom: 0;
  width: 1px;
}

.plot__cross--y {
  left: 0;
  right: 0;
  height: 1px;
}

.plot__dot {
  position: absolute;
  width: 24rpx;
  height: 24rpx;
  margin-left: -12rpx;
  margin-top: -12rpx;
  border-radius: 50%;
  background: $xc-purple;
  box-shadow: 0 0 16rpx rgba(155, 126, 216, 0.4);
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
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.5);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>
