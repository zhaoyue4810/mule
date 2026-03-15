<script setup lang="ts">
import { computed, getCurrentInstance, nextTick, onMounted, ref, watch } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const instance = getCurrentInstance();
const canvasId = `scratch-${Math.random().toString(36).slice(2, 8)}`;
const flash = ref(false);
const revealed = ref(false);
const autoCommitted = ref(false);
const maskRect = ref<{ left: number; top: number; width: number; height: number } | null>(null);
const scratching = ref(false);
const clearRatio = ref(0);
const lastSoundAt = ref(0);

const gridCols = 28;
const gridRows = 16;
const totalCells = gridCols * gridRows;
const clearedCells = ref<boolean[]>(Array.from({ length: totalCells }, () => false));

const config = computed<Record<string, unknown>>(
  () => (props.question.config as Record<string, unknown> | null) || {},
);
const revealThreshold = computed(() => {
  const value = Number(config.value.reveal_threshold ?? 0.35);
  if (!Number.isFinite(value)) {
    return 0.35;
  }
  return Math.min(0.95, Math.max(0.1, value));
});
const stageHeight = computed(() => {
  const value = Number(config.value.canvas_height ?? 250);
  if (!Number.isFinite(value) || value <= 0) {
    return 250;
  }
  return value;
});
const selectedOptionCode = computed(
  () =>
    props.modelValue ||
    props.question.options[0]?.option_code ||
    (props.question.options[0] ? String(props.question.options[0].seq) : ""),
);
const selectedOption = computed(
  () =>
    props.question.options.find(
      (item) => (item.option_code || String(item.seq)) === selectedOptionCode.value,
    ) || props.question.options[0],
);
const progressText = computed(() => `${Math.round(clearRatio.value * 100)}%`);

function triggerFlash() {
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
}

function resetState() {
  revealed.value = false;
  autoCommitted.value = false;
  clearRatio.value = 0;
  scratching.value = false;
  maskRect.value = null;
  clearedCells.value = Array.from({ length: totalCells }, () => false);
}

function getContext() {
  const proxy = instance?.proxy;
  if (!proxy) {
    return null;
  }
  return uni.createCanvasContext(canvasId, proxy);
}

function drawMask() {
  const ctx = getContext();
  if (!ctx) {
    return;
  }
  const width = 640;
  const height = 360;
  ctx.clearRect(0, 0, width, height);
  const gradient = ctx.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "#C0C0C0");
  gradient.addColorStop(0.3, "#D8D8D8");
  gradient.addColorStop(0.5, "#A8A8A8");
  gradient.addColorStop(0.7, "#D0D0D0");
  gradient.addColorStop(1, "#B0B0B0");
  ctx.setFillStyle(gradient);
  ctx.fillRect(0, 0, width, height);
  (ctx as unknown as { setGlobalAlpha?: (value: number) => void }).setGlobalAlpha?.(0.08);
  for (let i = 0; i < width + height; i += 4) {
    ctx.setStrokeStyle("#FFFFFF");
    ctx.setLineWidth(1);
    ctx.beginPath();
    ctx.moveTo(i, 0);
    ctx.lineTo(0, i);
    ctx.stroke();
  }
  (ctx as unknown as { setGlobalAlpha?: (value: number) => void }).setGlobalAlpha?.(1);
  ctx.draw();
}

async function ensureMaskRect() {
  if (maskRect.value) {
    return maskRect.value;
  }
  const proxy = instance?.proxy;
  if (!proxy) {
    return null;
  }
  return new Promise<{ left: number; top: number; width: number; height: number } | null>(
    (resolve) => {
      uni.createSelectorQuery()
        .in(proxy)
        .select(".scratch__canvas")
        .boundingClientRect((rect) => {
          const target = Array.isArray(rect) ? rect[0] : rect;
          if (
            target &&
            typeof target.left === "number" &&
            typeof target.top === "number" &&
            typeof target.width === "number" &&
            typeof target.height === "number"
          ) {
            maskRect.value = {
              left: target.left,
              top: target.top,
              width: target.width,
              height: target.height,
            };
            resolve(maskRect.value);
            return;
          }
          resolve(null);
        })
        .exec();
    },
  );
}

function markCells(localX: number, localY: number, width: number, height: number, radius = 30) {
  const xStart = Math.floor(((localX - radius) / width) * gridCols);
  const xEnd = Math.ceil(((localX + radius) / width) * gridCols);
  const yStart = Math.floor(((localY - radius) / height) * gridRows);
  const yEnd = Math.ceil(((localY + radius) / height) * gridRows);
  for (let row = yStart; row <= yEnd; row += 1) {
    for (let col = xStart; col <= xEnd; col += 1) {
      if (row < 0 || row >= gridRows || col < 0 || col >= gridCols) {
        continue;
      }
      const index = row * gridCols + col;
      if (!clearedCells.value[index]) {
        clearedCells.value[index] = true;
      }
    }
  }
  const clearedCount = clearedCells.value.filter(Boolean).length;
  clearRatio.value = clearedCount / totalCells;
}

function eraseAt(localX: number, localY: number) {
  const ctx = getContext();
  if (!ctx) {
    return;
  }
  ctx.save();
  (ctx as unknown as { globalCompositeOperation: string }).globalCompositeOperation =
    "destination-out";
  ctx.beginPath();
  ctx.arc(localX, localY, 30, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  ctx.draw(true);
}

function maybeCommit() {
  if (autoCommitted.value || clearRatio.value < revealThreshold.value || !selectedOptionCode.value) {
    return;
  }
  autoCommitted.value = true;
  revealed.value = true;
  haptic(15);
  playSound("chime");
  triggerFlash();
  setTimeout(() => {
    emit("update:modelValue", selectedOptionCode.value);
  }, 220);
}

function touchPoint(event: {
  touches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
  changedTouches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
}) {
  const touch = event.touches?.[0] || event.changedTouches?.[0];
  if (!touch) return null;
  const x = touch.clientX ?? touch.pageX ?? touch.x;
  const y = touch.clientY ?? touch.pageY ?? touch.y;
  if (typeof x !== "number" || typeof y !== "number") return null;
  return { x, y };
}

async function onScratchMove(event: {
  touches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
  changedTouches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
}) {
  if (revealed.value || !scratching.value) {
    return;
  }
  const point = touchPoint(event);
  if (!point) {
    return;
  }
  const rect = await ensureMaskRect();
  if (!rect || rect.width <= 0 || rect.height <= 0) {
    return;
  }
  const localX = point.x - rect.left;
  const localY = point.y - rect.top;
  if (localX < 0 || localX > rect.width || localY < 0 || localY > rect.height) {
    return;
  }
  const canvasX = (localX / rect.width) * 640;
  const canvasY = (localY / rect.height) * 360;
  eraseAt(canvasX, canvasY);
  markCells(localX, localY, rect.width, rect.height);
  if (Date.now() - lastSoundAt.value > 140) {
    playSound("ding");
    lastSoundAt.value = Date.now();
  }
  maybeCommit();
}

function onScratchStart() {
  scratching.value = true;
}

function onScratchEnd() {
  scratching.value = false;
}

watch(
  () => props.question.seq,
  async () => {
    resetState();
    await nextTick();
    drawMask();
    await ensureMaskRect();
  },
  { immediate: true },
);

onMounted(async () => {
  await nextTick();
  drawMask();
  await ensureMaskRect();
});
</script>

<template>
  <view class="scratch q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="scratch__card" :style="{ minHeight: `${stageHeight}rpx` }">
      <view class="scratch__reveal-layer">
        <text class="scratch__emoji">{{ selectedOption?.emoji || "🎁" }}</text>
        <text class="scratch__label">{{ selectedOption?.label || "命运彩蛋" }}</text>
      </view>
      <canvas
        v-show="!revealed"
        :canvas-id="canvasId"
        :id="canvasId"
        class="scratch__canvas"
        @touchstart.stop.prevent="onScratchStart"
        @touchmove.stop.prevent="onScratchMove"
        @touchend.stop.prevent="onScratchEnd"
        @touchcancel.stop.prevent="onScratchEnd"
      />
      <text class="scratch__hint">{{ revealed ? "已揭晓" : `刮开进度：${progressText}` }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.scratch {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.scratch__card {
  position: relative;
  padding: 20rpx;
  border-radius: 26rpx;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(237, 229, 249, 0.48));
  border: 1px solid rgba(155, 126, 216, 0.12);
  overflow: hidden;
}

.scratch__reveal-layer {
  position: absolute;
  inset: 20rpx;
  border-radius: 22rpx;
  background: linear-gradient(160deg, rgba(155, 126, 216, 0.15), rgba(232, 114, 154, 0.15));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.scratch__emoji {
  font-size: 54rpx;
}

.scratch__label {
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.scratch__canvas {
  position: relative;
  z-index: 2;
  width: 640rpx;
  height: 360rpx;
  border-radius: 22rpx;
}

.scratch__hint {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 12rpx;
  z-index: 3;
  text-align: center;
  font-size: 22rpx;
  color: $xc-muted;
}

.edge-flash {
  position: absolute;
  inset: 0;
  pointer-events: none;
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
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.56);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>
