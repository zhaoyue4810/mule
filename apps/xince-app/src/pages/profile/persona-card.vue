<script setup lang="ts">
import { nextTick, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import PersonaRadarCanvas from "@/components/profile/PersonaRadarCanvas.vue";
import type { PersonaCardPayload } from "@/shared/models/persona";
import { fetchPersonaCard } from "@/shared/services/persona";

const card = ref<PersonaCardPayload | null>(null);
const loading = ref(true);
const error = ref("");
const imageUrl = ref("");

async function loadCard() {
  loading.value = true;
  error.value = "";
  try {
    card.value = await fetchPersonaCard();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "人设名片加载失败";
  } finally {
    loading.value = false;
  }
}

async function saveCard() {
  if (!card.value) {
    return;
  }
  await nextTick();
  const ctx = uni.createCanvasContext("personaCardCanvas");
  ctx.setFillStyle("#FBF7F4");
  ctx.fillRect(0, 0, 720, 1180);
  ctx.setFillStyle("rgba(255,255,255,0.86)");
  ctx.fillRect(48, 48, 624, 1084);
  ctx.setFillStyle("#9B7ED8");
  ctx.setFontSize(24);
  ctx.fillText("XinCe Persona Card", 70, 94);
  ctx.setFillStyle("#3A2E42");
  ctx.setFontSize(50);
  ctx.fillText(card.value.avatar_value, 70, 170);
  ctx.setFontSize(34);
  ctx.fillText(card.value.nickname, 140, 164);
  ctx.setFontSize(26);
  ctx.setFillStyle("#7B6E85");
  ctx.fillText(card.value.persona_title, 140, 206);
  ctx.setFillStyle("#3A2E42");
  ctx.setFontSize(24);
  ctx.fillText(card.value.soul_signature.slice(0, 30), 70, 284);
  let y = 380;
  card.value.dimensions.forEach((item) => {
    ctx.setFillStyle("#7B6E85");
    ctx.fillText(item.label, 70, y);
    ctx.setFillStyle("rgba(155, 126, 216,0.18)");
    ctx.fillRect(160, y - 18, 380, 16);
    ctx.setFillStyle("#9B7ED8");
    ctx.fillRect(160, y - 18, (380 * item.score) / 100, 16);
    ctx.setFillStyle("#3A2E42");
    ctx.fillText(`${Math.round(item.score)}%`, 566, y);
    y += 72;
  });
  ctx.setFillStyle("#3A2E42");
  ctx.setFontSize(28);
  ctx.fillText(`${card.value.weather.emoji} ${card.value.weather.title}`, 70, 820);
  ctx.setFillStyle("#7B6E85");
  ctx.setFontSize(22);
  ctx.fillText(card.value.weather.description.slice(0, 36), 70, 864);
  ctx.setFillStyle("#9B7ED8");
  ctx.fillText(card.value.keywords.join(" · "), 70, 940);
  await new Promise<void>((resolve) => ctx.draw(false, resolve));
  const tempPath = await new Promise<string>((resolve, reject) => {
    uni.canvasToTempFilePath({
      canvasId: "personaCardCanvas",
      width: 720,
      height: 1180,
      destWidth: 1080,
      destHeight: 1770,
      success: (res) => resolve(res.tempFilePath),
      fail: reject,
    });
  });
  imageUrl.value = tempPath;
  // #ifdef H5
  if (typeof document !== "undefined") {
    const link = document.createElement("a");
    link.href = tempPath;
    link.download = `xince-persona-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    return;
  }
  // #endif
  await uni.saveImageToPhotosAlbum({ filePath: tempPath });
  uni.showToast({ title: "已保存到相册", icon: "success" });
}

onLoad(() => {
  void loadCard();
});
</script>

<template>
  <view class="page">
    <view v-if="loading" class="panel"><text class="panel__body">正在加载人设名片...</text></view>
    <view v-else-if="error" class="panel"><text class="panel__body">{{ error }}</text></view>
    <view v-else-if="card" class="stack">
      <view class="card">
        <text class="card__avatar">{{ card.avatar_value }}</text>
        <text class="card__name">{{ card.nickname }}</text>
        <text class="card__title">{{ card.persona_title }}</text>
        <text class="card__signature">{{ card.soul_signature }}</text>
      </view>
      <PersonaRadarCanvas :dimensions="card.dimensions" />
      <view class="panel">
        <text class="panel__title">维度条形图</text>
        <view class="bars">
          <view v-for="item in card.dimensions" :key="item.dim_code" class="bar">
            <text class="bar__label">{{ item.label }}</text>
            <view class="bar__track"><view class="bar__fill" :style="{ width: `${item.score}%` }" /></view>
            <text class="bar__value">{{ Math.round(item.score) }}%</text>
          </view>
        </view>
      </view>
      <view class="panel">
        <text class="panel__title">灵魂天气</text>
        <text class="panel__body">{{ card.weather.emoji }} {{ card.weather.title }} · {{ card.weather.description }}</text>
      </view>
      <view class="panel">
        <text class="panel__title">关键词</text>
        <view class="keywords"><text v-for="item in card.keywords" :key="item" class="keyword">{{ item }}</text></view>
      </view>
      <button class="button" @tap="saveCard">保存名片</button>
      <canvas canvas-id="personaCardCanvas" id="personaCardCanvas" class="canvas" style="width:720px;height:1180px" />
    </view>
  </view>
</template>

<style scoped lang="scss">
.page { padding: 28rpx; }
.stack { display: flex; flex-direction: column; gap: 18rpx; }
.panel, .card {
  padding: 28rpx;
  border-radius: 26rpx;
  background: rgba(255,255,255,0.9);
  border: 2rpx solid rgba(155, 126, 216,0.08);
}
.card {
  text-align: center;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(237, 229, 249, 0.36));
}
.card__avatar { display:block; font-size:72rpx; }
.card__name { display:block; margin-top:12rpx; font-size:36rpx; font-weight:700; }
.card__title { display:block; margin-top:8rpx; font-size:26rpx; color:$xc-accent; }
.card__signature, .panel__body { display:block; margin-top:14rpx; font-size:24rpx; line-height:1.7; color:$xc-muted; }
.panel__title { display:block; font-size:28rpx; font-weight:700; }
.bars { display:flex; flex-direction:column; gap:14rpx; margin-top:18rpx; }
.bar { display:grid; grid-template-columns: 110rpx 1fr 90rpx; gap: 14rpx; align-items:center; }
.bar__label, .bar__value { font-size:22rpx; }
.bar__track { height: 16rpx; border-radius:999rpx; background:rgba(58, 46, 66, 0.08); overflow:hidden; }
.bar__fill { height:100%; border-radius:inherit; background:linear-gradient(135deg,#9B7ED8,#C9B5F0); }
.keywords { display:flex; flex-wrap:wrap; gap:12rpx; margin-top:16rpx; }
.keyword { padding:10rpx 18rpx; border-radius:999rpx; background:rgba(237, 229, 249, 0.72); color:$xc-accent; font-size:22rpx; }
.button { border-radius:999rpx; background:linear-gradient(135deg,#9B7ED8,#7C5DBF); color:#fff9f3; }
.canvas { position: fixed; left: -9999px; top: -9999px; pointer-events:none; }
</style>
