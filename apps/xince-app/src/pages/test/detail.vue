<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import type { PublishedTestDetail } from "@/shared/models/tests";
import { SoundManager } from "@/shared/utils/sound-manager";
import { useTestCatalogStore } from "@/stores/test-catalog";

const store = useTestCatalogStore();

const detail = ref<PublishedTestDetail | null>(null);
const loading = ref(true);
const error = ref("");

const dimensionText = computed(() =>
  detail.value?.dimensions.map((item) => item.dim_name).join(" / ") || "待补充维度",
);

const heroClass = computed(() => {
  const cat = detail.value?.category || "";
  if (cat.includes("性格")) return "bg-purple";
  if (cat.includes("情感")) return "bg-pink";
  if (cat.includes("关系")) return "bg-peach";
  if (cat.includes("职业")) return "bg-gold";
  return "bg-mint";
});

const heroEmoji = computed(() => {
  const cat = detail.value?.category || "";
  if (cat.includes("性格")) return "🧠";
  if (cat.includes("情感")) return "💗";
  if (cat.includes("关系")) return "🤝";
  if (cat.includes("职业")) return "💼";
  return "✨";
});

async function loadDetail(testCode: string) {
  loading.value = true;
  error.value = "";
  try {
    detail.value = await store.loadDetail(testCode);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "测试详情加载失败";
  } finally {
    loading.value = false;
  }
}

function startTest() {
  if (!detail.value) {
    return;
  }
  if (SoundManager.isSoundEnabled()) {
    SoundManager.play("whoosh");
  }
  uni.navigateTo({
    url: `/pages/test/answer?testCode=${detail.value.test_code}`,
  });
}

onLoad((query) => {
  const testCode =
    query && typeof query.testCode === "string" ? query.testCode : "";
  if (!testCode) {
    error.value = "缺少 testCode 参数";
    loading.value = false;
    return;
  }

  loadDetail(testCode);
});
</script>

<template>
  <view class="page">
    <view v-if="loading" class="state-card">
      <text class="state-card__text">正在加载测试详情...</text>
    </view>

    <view v-else-if="error" class="state-card state-card--error">
      <text class="state-card__text">{{ error }}</text>
    </view>

    <view v-else-if="detail" class="detail">
      <view class="detail__hero" :class="heroClass">
        <view class="detail__back" @tap="uni.navigateBack()">
          <text>‹</text>
        </view>
        <text class="detail__emoji">{{ heroEmoji }}</text>
        <text class="detail__category">{{ detail.category }}</text>
        <text class="detail__title">{{ detail.name }}</text>
        <text class="detail__summary">
          {{ detail.question_count }} 题 · {{ detail.duration_hint || "约5分钟" }} · v{{ detail.version }}
        </text>
      </view>

      <view class="detail__section anim-fu d1">
        <text class="detail__section-title">测试说明</text>
        <text class="detail__body">
          {{ detail.description || "当前已接通发布内容详情，后续会继续补充完整答题体验与报告链路。" }}
        </text>
      </view>

      <view class="detail__grid anim-fu d2">
        <view class="metric">
          <text class="metric__value">{{ detail.dimension_count }}</text>
          <text class="metric__label">维度</text>
        </view>
        <view class="metric">
          <text class="metric__value">{{ detail.persona_count }}</text>
          <text class="metric__label">人格</text>
        </view>
        <view class="metric">
          <text class="metric__value">{{ detail.participant_count }}</text>
          <text class="metric__label">体验人数</text>
        </view>
      </view>

      <view class="detail__section anim-fu d3">
        <text class="detail__section-title">维度结构</text>
        <text class="detail__body">{{ dimensionText }}</text>
      </view>

      <view v-if="detail.personas.length" class="detail__section anim-fu d4">
        <text class="detail__section-title">人格预览</text>
        <view class="persona-list">
          <view
            v-for="persona in detail.personas"
            :key="persona.persona_key"
            class="persona"
          >
            <text class="persona__name">{{ persona.persona_name }}</text>
            <text class="persona__keywords">{{ persona.keywords.join(" / ") || "待补充关键词" }}</text>
          </view>
        </view>
      </view>

      <button class="detail__button anim-fu d5" @tap="startTest">
        <text>🚀</text>
        <text>开始测试</text>
      </button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  animation: fadeInUp 0.45s $xc-ease both;
}

.state-card {
  margin: 28rpx;
  padding: 32rpx;
  border-radius: $xc-r-lg;
  @include glass;
  text-align: center;
}

.state-card--error {
  background: rgba(255, 240, 235, 0.92);
}

.state-card__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.detail {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  padding-bottom: 40rpx;
}

/* --- Hero Header --- */
.detail__hero {
  position: relative;
  padding: 80rpx 28rpx 40rpx;
  text-align: center;
  overflow: hidden;
  border-radius: 0 0 $xc-r-xl $xc-r-xl;

  &::before {
    content: "";
    position: absolute;
    inset: 0;
  }

  &.bg-purple::before {
    background: linear-gradient(160deg, #7C5DBF, #B57FE0, #C9B5F0);
  }

  &.bg-pink::before {
    background: linear-gradient(160deg, #D4548A, #E8729A, #F4A5BF);
  }

  &.bg-peach::before {
    background: linear-gradient(160deg, #D4894D, #F2A68B, #F8C9B5);
  }

  &.bg-mint::before {
    background: linear-gradient(160deg, #4DA68C, #7CC5B2, #A8DDD0);
  }

  &.bg-gold::before {
    background: linear-gradient(160deg, #B8923A, #D4A853, #E5C97E);
  }
}

.detail__back {
  position: absolute;
  top: 24rpx;
  left: 20rpx;
  z-index: 2;
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: $xc-white;
  font-size: 36rpx;
  // #ifdef H5
  backdrop-filter: blur(8px);
  // #endif

  &:active {
    background: rgba(255, 255, 255, 0.35);
  }
}

.detail__emoji {
  position: relative;
  z-index: 1;
  font-size: 80rpx;
  animation: heartbeat 2s ease-in-out infinite;
}

.detail__category {
  display: block;
  position: relative;
  z-index: 1;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.78);
}

.detail__title {
  display: block;
  position: relative;
  z-index: 1;
  margin-top: 10rpx;
  font-family: $xc-font-serif;
  font-size: 38rpx;
  font-weight: 900;
  color: $xc-white;
}

.detail__summary {
  display: block;
  position: relative;
  z-index: 1;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.75);
}

/* --- Sections --- */
.detail__section {
  margin: 0 24rpx;
  padding: 24rpx;
  border-radius: $xc-r;
  @include glass;
  box-shadow: $xc-sh-md;
}

.detail__section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
}

.detail__body {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 1.75;
  color: $xc-muted;
}

/* --- Metrics Grid --- */
.detail__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14rpx;
  margin: 0 24rpx;
}

.metric {
  padding: 24rpx 16rpx;
  border-radius: $xc-r;
  @include glass;
  box-shadow: $xc-sh-md;
  text-align: center;
}

.metric__value {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  @include text-gradient;
}

.metric__label {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-hint;
}

/* --- Persona List --- */
.persona-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 16rpx;
}

.persona {
  padding: 20rpx;
  border-radius: $xc-r;
  background: linear-gradient(135deg, rgba(237, 229, 249, 0.4), rgba(253, 230, 239, 0.3));
  border: 1px solid rgba(155, 126, 216, 0.08);
  transition: transform 0.2s $xc-ease;

  &:active {
    transform: scale(0.98);
  }
}

.persona__name {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}

.persona__keywords {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

/* --- CTA Button --- */
.detail__button {
  margin: 8rpx 24rpx 0;
  height: 88rpx;
  border-radius: 999rpx;
  @include btn-primary;
  font-size: 30rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  position: relative;
  overflow: hidden;

  &::after {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.25), transparent);
    background-size: 200% 100%;
    animation: shimmer 2.5s infinite;
  }
}

/* --- Cascade animations --- */
.anim-fu {
  animation: fadeInUp 0.5s $xc-ease both;
}

.d1 {
  animation-delay: 0.06s;
}

.d2 {
  animation-delay: 0.12s;
}

.d3 {
  animation-delay: 0.18s;
}

.d4 {
  animation-delay: 0.24s;
}

.d5 {
  animation-delay: 0.3s;
}
</style>
