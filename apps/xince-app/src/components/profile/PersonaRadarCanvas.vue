<script setup lang="ts">
import { getCurrentInstance, nextTick, onMounted, watch } from "vue";

import type { PersonaCardDimensionItem } from "@/shared/models/persona";

const props = defineProps<{
  dimensions: PersonaCardDimensionItem[];
}>();

const instance = getCurrentInstance();
const canvasId = `persona-radar-${Math.random().toString(36).slice(2, 8)}`;

function pointAt(cx: number, cy: number, radius: number, angle: number, value: number) {
  const scaled = (Math.max(0, Math.min(value, 100)) / 100) * radius;
  return {
    x: cx + Math.cos(angle) * scaled,
    y: cy + Math.sin(angle) * scaled,
  };
}

function draw() {
  if (!instance?.proxy) {
    return;
  }
  const ctx = uni.createCanvasContext(canvasId, instance.proxy);
  const width = 320;
  const height = 320;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 110;
  const dimensions = props.dimensions.slice(0, 5);
  ctx.clearRect(0, 0, width, height);
  ctx.setFillStyle("#FBF7F4");
  ctx.fillRect(0, 0, width, height);

  for (let step = 1; step <= 4; step += 1) {
    ctx.beginPath();
    dimensions.forEach((item, index) => {
      const angle = -Math.PI / 2 + (Math.PI * 2 * index) / dimensions.length;
      const point = pointAt(centerX, centerY, radius, angle, (step / 4) * 100);
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    });
    ctx.closePath();
    ctx.setStrokeStyle("rgba(155, 126, 216,0.14)");
    ctx.stroke();
  }

  dimensions.forEach((item, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / dimensions.length;
    const edge = pointAt(centerX, centerY, radius, angle, 100);
    const label = pointAt(centerX, centerY, radius + 22, angle, 100);
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(edge.x, edge.y);
    ctx.setStrokeStyle("rgba(155, 126, 216,0.14)");
    ctx.stroke();
    ctx.setFillStyle("#7B6E85");
    ctx.setFontSize(12);
    ctx.setTextAlign("center");
    ctx.fillText(item.label, label.x, label.y);
  });

  ctx.beginPath();
  dimensions.forEach((item, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / dimensions.length;
    const point = pointAt(centerX, centerY, radius, angle, item.score);
    if (index === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      ctx.lineTo(point.x, point.y);
    }
  });
  ctx.closePath();
  ctx.setStrokeStyle("#9B7ED8");
  ctx.setFillStyle("rgba(155, 126, 216,0.24)");
  ctx.setLineWidth(2);
  ctx.stroke();
  ctx.fill();
  ctx.draw();
}

onMounted(() => {
  void nextTick(draw);
});

watch(
  () => props.dimensions,
  () => {
    void nextTick(draw);
  },
  { deep: true },
);
</script>

<template>
  <view class="radar">
    <canvas :id="canvasId" :canvas-id="canvasId" class="radar__canvas" />
  </view>
</template>

<style scoped lang="scss">
.radar {
  padding: 18rpx;
  border-radius: 28rpx;
  background: $xc-card;
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.radar__canvas {
  width: 640rpx;
  height: 640rpx;
}
</style>
