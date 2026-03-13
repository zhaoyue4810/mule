<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import type {
  AppProfileOverview,
  ProfileReportHistoryItem,
} from "@/shared/models/profile";
import type { AuthUserPayload } from "@/shared/models/auth";
import {
  bindPhone,
  ensureAppSession,
  getSessionUser,
  sendPhoneCode,
} from "@/shared/services/auth";
import { fetchMyProfileOverview, fetchMyProfileReports } from "@/shared/services/profile";

const overview = ref<AppProfileOverview | null>(null);
const reports = ref<ProfileReportHistoryItem[]>([]);
const loading = ref(false);
const error = ref("");
const sessionUser = ref<AuthUserPayload | null>(null);
const phone = ref("");
const code = ref("");
const sendingCode = ref(false);
const bindingPhone = ref(false);
const debugCode = ref("");

const hasProfile = computed(() => Boolean(overview.value));
const canSubmitPhoneBind = computed(
  () => phone.value.trim().length >= 11 && code.value.trim().length >= 4,
);

function formatTime(value?: string | null) {
  if (!value) {
    return "暂未记录";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  const hour = `${date.getHours()}`.padStart(2, "0");
  const minute = `${date.getMinutes()}`.padStart(2, "0");
  return `${month}-${day} ${hour}:${minute}`;
}

function openReport(recordId: number) {
  uni.navigateTo({
    url: `/pages/test/result?recordId=${recordId}`,
  });
}

function goHome() {
  uni.switchTab({
    url: "/pages/home/index",
  });
}

async function loadProfile() {
  overview.value = null;
  reports.value = [];
  error.value = "";

  loading.value = true;
  try {
    sessionUser.value = await ensureAppSession();
    const [overviewPayload, reportPayload] = await Promise.all([
      fetchMyProfileOverview(),
      fetchMyProfileReports(),
    ]);
    overview.value = overviewPayload;
    reports.value = reportPayload;
  } catch (err) {
    if (
      err instanceof Error &&
      (err.message.includes("Authorization required") ||
        err.message.includes("Token"))
    ) {
      sessionUser.value = await ensureAppSession();
      return;
    }
    error.value = err instanceof Error ? err.message : "个人中心加载失败";
  } finally {
    loading.value = false;
  }
}

async function sendCode() {
  if (sendingCode.value || phone.value.trim().length < 11) {
    return;
  }
  sendingCode.value = true;
  try {
    const payload = await sendPhoneCode(phone.value.trim());
    debugCode.value = payload.debug_code || "";
    uni.showToast({
      title: payload.debug_code ? `验证码 ${payload.debug_code}` : "验证码已发送",
      icon: "none",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "发送失败",
      icon: "none",
    });
  } finally {
    sendingCode.value = false;
  }
}

async function submitPhoneBind() {
  if (bindingPhone.value || !canSubmitPhoneBind.value) {
    return;
  }
  bindingPhone.value = true;
  try {
    const session = await bindPhone(phone.value.trim(), code.value.trim());
    sessionUser.value = session.user;
    code.value = "";
    debugCode.value = "";
    await loadProfile();
    uni.showToast({
      title: "手机号已绑定",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "绑定失败",
      icon: "none",
    });
  } finally {
    bindingPhone.value = false;
  }
}

onShow(() => {
  sessionUser.value = getSessionUser();
  loadProfile();
});
</script>

<template>
  <view class="page">
    <view v-if="!hasProfile && !loading && !error" class="panel panel--empty">
      <text class="panel__title">你的旅程还没开始</text>
      <text class="panel__body">
        当前设备还没有生成过测试记录。先去完成一套已发布测试，这里就会自动出现你的历史结果和基础画像。
      </text>
      <button class="panel__button" @tap="goHome">去首页开始测试</button>
    </view>

    <view v-else-if="loading" class="panel">
      <text class="panel__body">正在加载你的记录与画像...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__title">加载失败</text>
      <text class="panel__body">{{ error }}</text>
      <button class="panel__button" @tap="loadProfile">重新加载</button>
    </view>

    <view v-else-if="overview" class="profile">
      <view class="hero">
        <text class="hero__avatar">{{ overview.avatar_value }}</text>
        <text class="hero__eyebrow">Memory Profile</text>
        <text class="hero__title">{{ overview.nickname }}</text>
        <text class="hero__meta">
          已完成 {{ overview.test_count }} 次测试 · 覆盖 {{ overview.distinct_test_count }} 套内容
        </text>
        <text class="hero__submeta">
          最近一次：{{ formatTime(overview.last_test_at) }}
        </text>
      </view>

      <view class="stats">
        <view class="stat-card">
          <text class="stat-card__label">平均用时</text>
          <text class="stat-card__value">{{ overview.avg_duration_seconds }} 秒</text>
        </view>
        <view class="stat-card">
          <text class="stat-card__label">高频画像</text>
          <text class="stat-card__value">
            {{ overview.persona_distribution[0]?.persona_name || "待生成" }}
          </text>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">账号与登录</text>
        <text class="panel__body" v-if="sessionUser?.has_phone">
          当前账号已绑定手机号 {{ sessionUser.masked_phone || "已绑定" }}，后续可直接用验证码登录并同步历史记录。
        </text>
        <view v-else class="account-form">
          <text class="panel__body">
            绑定手机号后，你的访客记录会升级到正式账号，换设备也能找回历史测试和报告。
          </text>
          <input
            v-model="phone"
            class="field-input"
            type="number"
            maxlength="11"
            placeholder="输入手机号"
          />
          <view class="field-row">
            <input
              v-model="code"
              class="field-input field-input--grow"
              type="number"
              maxlength="6"
              placeholder="输入验证码"
            />
            <button class="field-button" :disabled="sendingCode" @tap="sendCode">
              {{ sendingCode ? "发送中" : "发送验证码" }}
            </button>
          </view>
          <text v-if="debugCode" class="panel__body panel__body--accent">
            当前演示验证码：{{ debugCode }}
          </text>
          <button
            class="panel__button"
            :disabled="!canSubmitPhoneBind || bindingPhone"
            @tap="submitPhoneBind"
          >
            {{ bindingPhone ? "绑定中..." : "绑定手机号" }}
          </button>
        </view>
      </view>

      <view class="panel" v-if="overview.dominant_dimensions.length">
        <text class="panel__title">基础画像聚合</text>
        <text class="panel__body">
          当前阶段先基于你已完成的报告，聚合出最稳定浮现的核心维度。
        </text>
        <view class="chips">
          <view
            v-for="item in overview.dominant_dimensions"
            :key="item.dim_code"
            class="chip"
          >
            <text class="chip__name">{{ item.dim_code }}</text>
            <text class="chip__score">{{ item.total_score.toFixed(2) }}</text>
          </view>
        </view>
      </view>

      <view class="panel" v-if="overview.persona_distribution.length">
        <text class="panel__title">人格分布</text>
        <view class="rows">
          <view
            v-for="item in overview.persona_distribution"
            :key="`${item.persona_key || 'unknown'}-${item.count}`"
            class="row"
          >
            <text class="row__name">{{ item.persona_name || "未命名人格" }}</text>
            <text class="row__value">{{ item.count }} 次</text>
          </view>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">历史报告</text>
        <view v-if="reports.length" class="history">
          <view
            v-for="item in reports"
            :key="item.record_id"
            class="history-card"
            @tap="openReport(item.record_id)"
          >
            <view class="history-card__top">
              <text class="history-card__title">{{ item.test_name }}</text>
              <text class="history-card__time">{{ formatTime(item.completed_at) }}</text>
            </view>
            <text class="history-card__persona">
              {{ item.persona_name || "已生成基础结果" }}
            </text>
            <text class="history-card__summary">
              {{ item.summary || "当前报告还没有生成摘要文案。" }}
            </text>
            <text class="history-card__footer">
              {{ item.duration_seconds || 0 }} 秒 · 点击查看报告
            </text>
          </view>
        </view>
        <text v-else class="panel__body">你还没有可回看的历史报告。</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx 28rpx 40rpx;
}

.profile {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.hero {
  padding: 36rpx 30rpx;
  border-radius: 28rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 241, 223, 0.98), rgba(255, 215, 184, 0.92)),
    #fff8f1;
  box-shadow: $xc-shadow;
}

.hero__avatar {
  display: inline-flex;
  width: 88rpx;
  height: 88rpx;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.72);
  font-size: 44rpx;
}

.hero__eyebrow {
  display: block;
  margin-top: 20rpx;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: $xc-accent;
  text-transform: uppercase;
}

.hero__title {
  display: block;
  margin-top: 12rpx;
  font-size: 40rpx;
  font-weight: 700;
}

.hero__meta,
.hero__submeta {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: rgba(43, 33, 24, 0.72);
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.panel {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.85);
  border: 2rpx solid $xc-line;
}

.panel__title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
}

.panel__body {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__body--accent {
  color: $xc-accent;
}

.panel__button {
  margin-top: 24rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #d96f3d, #bf5321);
  color: #fff8f0;
}

.account-form {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.field-row {
  display: flex;
  gap: 14rpx;
  align-items: center;
}

.field-input {
  width: 100%;
  min-height: 88rpx;
  padding: 0 24rpx;
  border-radius: 18rpx;
  background: rgba(255, 250, 244, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.12);
  font-size: 28rpx;
}

.field-input--grow {
  flex: 1;
}

.field-button {
  min-width: 220rpx;
  border-radius: 18rpx;
  background: rgba(217, 111, 61, 0.12);
  color: $xc-accent;
  font-size: 24rpx;
}

.stat-card {
  padding: 24rpx;
  border-radius: 22rpx;
  background: rgba(255, 253, 248, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
}

.stat-card__label {
  display: block;
  font-size: 22rpx;
  color: $xc-muted;
}

.stat-card__value {
  display: block;
  margin-top: 10rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: $xc-ink;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 18rpx;
}

.chip {
  min-width: 148rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 238, 224, 0.92);
}

.chip__name {
  display: block;
  font-size: 24rpx;
  color: $xc-muted;
}

.chip__score {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-accent;
}

.rows {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 18rpx;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 250, 244, 0.92);
}

.row__name,
.row__value {
  font-size: 24rpx;
}

.row__value {
  color: $xc-accent;
}

.history {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.history-card {
  padding: 24rpx;
  border-radius: 22rpx;
  background: rgba(255, 250, 244, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
}

.history-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.history-card__title {
  font-size: 28rpx;
  font-weight: 600;
}

.history-card__time,
.history-card__footer {
  font-size: 22rpx;
  color: $xc-muted;
}

.history-card__persona {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: $xc-accent;
}

.history-card__summary {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.history-card__footer {
  display: block;
  margin-top: 14rpx;
}
</style>
