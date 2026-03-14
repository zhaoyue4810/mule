<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import type { PublishedTestDetail } from "@/shared/models/tests";
import { useTestCatalogStore } from "@/stores/test-catalog";

const store = useTestCatalogStore();

const detail = ref<PublishedTestDetail | null>(null);
const loading = ref(true);
const error = ref("");

const dimensionText = computed(() =>
  detail.value?.dimensions.map((item) => item.dim_name).join(" / ") || "待补充维度",
);

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
      <view class="detail__hero">
        <text class="detail__category">{{ detail.category }}</text>
        <text class="detail__title">{{ detail.name }}</text>
        <text class="detail__summary">
          {{ detail.question_count }} 题 · {{ detail.duration_hint || "待补充时长" }} · v{{ detail.version }}
        </text>
      </view>

      <view class="detail__section">
        <text class="detail__section-title">测试说明</text>
        <text class="detail__body">
          {{ detail.description || "当前已接通发布内容详情，后续会继续补充完整答题体验与报告链路。" }}
        </text>
      </view>

      <view class="detail__grid">
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

      <view class="detail__section">
        <text class="detail__section-title">维度结构</text>
        <text class="detail__body">{{ dimensionText }}</text>
      </view>

      <view v-if="detail.personas.length" class="detail__section">
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

      <button class="detail__button" @tap="startTest">开始测试</button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx;
}

.state-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 2rpx solid $xc-line;
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
}

.detail__hero {
  padding: 34rpx 30rpx;
  border-radius: 28rpx;
  background: linear-gradient(160deg, #fff2e0, #ffdabb);
  box-shadow: $xc-shadow;
}

.detail__category {
  display: block;
  font-size: 22rpx;
  color: rgba(58, 46, 66, 0.7);
}

.detail__title {
  display: block;
  margin-top: 18rpx;
  font-size: 42rpx;
  font-weight: 700;
  line-height: 1.35;
}

.detail__summary {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: rgba(58, 46, 66, 0.72);
}

.detail__section {
  padding: 26rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 2rpx solid rgba(58, 46, 66, 0.06);
}

.detail__section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
}

.detail__body {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 1.75;
  color: $xc-muted;
}

.detail__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
}

.metric {
  padding: 24rpx 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 250, 244, 0.92);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  text-align: center;
}

.metric__value {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: $xc-accent;
}

.metric__label {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.persona-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 16rpx;
}

.persona {
  padding: 20rpx;
  border-radius: 20rpx;
  background: rgba(247, 212, 190, 0.26);
}

.persona__name {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
}

.persona__keywords {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.detail__button {
  margin-top: 8rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #9B7ED8, #7C5DBF);
  color: #fff9f3;
}
</style>
