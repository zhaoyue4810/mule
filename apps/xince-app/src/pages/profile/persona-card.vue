<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import PersonaRadarCanvas from "@/components/profile/PersonaRadarCanvas.vue";
import type { PersonaCardPayload } from "@/shared/models/persona";
import { fetchPersonaCard } from "@/shared/services/persona";

const card = ref<PersonaCardPayload | null>(null);
const loading = ref(true);
const error = ref("");
const imageUrl = ref("");
const saving = ref(false);

const topKeywords = computed(() => card.value?.keywords || []);
const hasDimensions = computed(() => Boolean(card.value?.dimensions.length));
const shareHints = computed(() => [
  "🪪 一张卡片看见你最稳定的灵魂标签",
  "📤 适合截图分享给朋友或放进社交资料里",
  "🔮 会随测试和匹配结果继续慢慢变化",
]);

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
  if (!card.value || saving.value) {
    return;
  }
  saving.value = true;
  try {
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
      uni.showToast({ title: "名片已下载", icon: "success" });
      return;
    }
    // #endif
    await uni.saveImageToPhotosAlbum({ filePath: tempPath });
    uni.showToast({ title: "已保存到相册", icon: "success" });
  } finally {
    saving.value = false;
  }
}

onLoad(() => {
  void loadCard();
});
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--pink" />
    <view v-if="loading" class="panel"><text class="panel__body">正在加载人设名片...</text></view>
    <view v-else-if="error" class="panel"><text class="panel__body">{{ error }}</text></view>
    <view v-else-if="card" class="stack">
      <view class="hero-card">
        <view class="hero-card__shine" />
        <view class="hero-card__top">
          <view class="hero-card__avatar">{{ card.avatar_value }}</view>
          <view class="hero-card__copy">
            <text class="hero-card__eyebrow">PERSONA CARD</text>
            <text class="hero-card__name">{{ card.nickname }}</text>
            <text class="hero-card__title">{{ card.persona_title }}</text>
          </view>
        </view>
        <text class="hero-card__signature">{{ card.soul_signature }}</text>
        <view class="hero-card__keywords">
          <text v-for="item in topKeywords" :key="item" class="hero-card__keyword">{{ item }}</text>
        </view>
        <button class="hero-card__button" :loading="saving" @tap="saveCard">
          {{ saving ? "生成中..." : "保存 / 分享名片" }}
        </button>
      </view>

      <view class="panel panel--radar">
        <view class="panel__head">
          <view>
            <text class="panel__eyebrow">DIMENSION RADAR</text>
            <text class="panel__title">灵魂坐标</text>
          </view>
          <text class="panel__meta">动态更新</text>
        </view>
        <view class="radar-panel">
          <view class="radar-panel__canvas">
            <PersonaRadarCanvas :dimensions="card.dimensions" />
            <view v-if="!hasDimensions" class="radar-panel__empty">
              <text class="radar-panel__empty-title">正在显影</text>
              <text class="radar-panel__empty-body">完成更多测试后，这里会开始长出你的专属维度轮廓。</text>
            </view>
          </view>
          <view class="radar-panel__weather">
            <text class="radar-panel__weather-emoji">{{ card.weather.emoji }}</text>
            <text class="radar-panel__weather-title">{{ card.weather.title }}</text>
            <text class="radar-panel__weather-body">{{ card.weather.description }}</text>
          </view>
        </view>
      </view>

      <view class="panel">
        <view class="panel__head">
          <view>
            <text class="panel__eyebrow">DIMENSION SCORES</text>
            <text class="panel__title">维度条形图</text>
          </view>
        </view>
        <view v-if="hasDimensions" class="bars">
          <view v-for="item in card.dimensions" :key="item.dim_code" class="bar">
            <view class="bar__top">
              <text class="bar__label">{{ item.label }}</text>
              <text class="bar__value">{{ Math.round(item.score) }}%</text>
            </view>
            <view class="bar__track">
              <view class="bar__fill" :style="{ width: `${item.score}%` }" />
            </view>
          </view>
        </view>
        <view v-else class="bars-empty">
          <text class="bars-empty__title">第一批维度还在生成</text>
          <text class="bars-empty__body">完成更多题目后，这里会按强弱顺序排出你的核心人格维度。</text>
        </view>
      </view>

      <view class="panel panel--tips">
        <text class="panel__title">分享提示</text>
        <view class="tips-list">
          <text v-for="item in shareHints" :key="item" class="tips-list__item">{{ item }}</text>
        </view>
        <text v-if="imageUrl" class="panel__body panel__body--accent">最近一次导出已生成，可直接继续分享。</text>
      </view>

      <canvas
        canvas-id="personaCardCanvas"
        id="personaCardCanvas"
        class="canvas"
        style="width:720px;height:1180px"
      />
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28rpx 24rpx 60rpx;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.96), rgba(255, 246, 239, 0.8) 42%, #fffaf6 100%);
}

.page__glow {
  position: absolute;
  width: 420rpx;
  height: 420rpx;
  border-radius: 50%;
  filter: blur(32px);
  opacity: 0.42;
  pointer-events: none;
}

.page__glow--violet {
  top: -120rpx;
  right: -120rpx;
  background: rgba(155, 126, 216, 0.24);
}

.page__glow--pink {
  left: -120rpx;
  bottom: 220rpx;
  background: rgba(232, 114, 154, 0.16);
}

.stack {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.panel,
.hero-card {
  @include card-base;
}

.hero-card {
  position: relative;
  overflow: hidden;
  padding: 30rpx;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(243, 235, 255, 0.92));
}

.hero-card__shine {
  position: absolute;
  top: -120rpx;
  right: -80rpx;
  width: 260rpx;
  height: 260rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
}

.hero-card__top {
  position: relative;
  display: flex;
  gap: 18rpx;
  align-items: center;
}

.hero-card__avatar {
  width: 132rpx;
  height: 132rpx;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.96), rgba(255, 236, 245, 0.78)),
    linear-gradient(135deg, rgba(155, 126, 216, 0.22), rgba(232, 114, 154, 0.14));
  box-shadow: 0 18rpx 36rpx rgba(155, 126, 216, 0.16);
  font-size: 62rpx;
}

.hero-card__copy {
  flex: 1;
  min-width: 0;
}

.hero-card__eyebrow,
.panel__eyebrow {
  display: block;
  font-size: 19rpx;
  letter-spacing: 2.6rpx;
  font-weight: 700;
  color: rgba(123, 110, 133, 0.76);
}

.hero-card__name {
  display: block;
  margin-top: 10rpx;
  font-size: 40rpx;
  font-weight: 800;
  color: $xc-ink;
}

.hero-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 25rpx;
  color: $xc-accent;
}

.hero-card__signature {
  position: relative;
  display: block;
  margin-top: 22rpx;
  font-size: 25rpx;
  line-height: 1.8;
  color: $xc-muted;
}

.hero-card__keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.hero-card__keyword {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 242, 231, 0.96);
  font-size: 22rpx;
  color: $xc-ink;
}

.hero-card__button {
  margin-top: 22rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #9B7ED8, #E8729A);
  color: #fffaf4;
}

.panel {
  padding: 28rpx;
}

.panel__head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  align-items: flex-start;
}

.panel__title {
  display: block;
  margin-top: 10rpx;
  font-size: 31rpx;
  font-weight: 800;
  color: $xc-ink;
}

.panel__meta {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(245, 238, 255, 0.9);
  font-size: 21rpx;
  color: $xc-purple;
}

.panel__body {
  display: block;
  margin-top: 14rpx;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__body--accent {
  color: $xc-accent;
}

.radar-panel {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 18rpx;
}

.radar-panel__canvas {
  position: relative;
  border-radius: 24rpx;
  overflow: hidden;
  background: rgba(255, 250, 244, 0.9);
}

.radar-panel__empty {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32rpx;
  text-align: center;
  background: rgba(255, 250, 244, 0.82);
}

.radar-panel__empty-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.radar-panel__empty-body {
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.radar-panel__weather {
  padding: 22rpx;
  border-radius: 24rpx;
  background:
    linear-gradient(145deg, rgba(255, 248, 242, 0.96), rgba(246, 240, 255, 0.9));
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.radar-panel__weather-emoji {
  display: block;
  font-size: 34rpx;
}

.radar-panel__weather-title {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.radar-panel__weather-body {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.bars {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.bar {
  padding: 18rpx 18rpx 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 248, 239, 0.95);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.bar__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.bar__label,
.bar__value {
  font-size: 24rpx;
}

.bar__label {
  font-weight: 700;
  color: $xc-ink;
}

.bar__value {
  color: $xc-accent;
}

.bar__track {
  height: 18rpx;
  margin-top: 14rpx;
  border-radius: 999rpx;
  background: rgba(58, 46, 66, 0.08);
  overflow: hidden;
}

.bar__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #9B7ED8, #E8729A);
}

.bars-empty {
  margin-top: 18rpx;
  padding: 26rpx 22rpx;
  border-radius: 22rpx;
  background: rgba(255, 248, 239, 0.95);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.bars-empty__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.bars-empty__body {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 18rpx;
}

.tips-list__item {
  padding: 18rpx 18rpx;
  border-radius: 20rpx;
  background: rgba(255, 248, 239, 0.94);
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-ink;
}

.canvas {
  position: fixed;
  left: -9999px;
  top: -9999px;
  pointer-events: none;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
