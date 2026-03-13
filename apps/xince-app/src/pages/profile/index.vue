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
const calendarHeatmapWeeks = computed(() => {
  const items = overview.value?.calendar_heatmap || [];
  const weeks: typeof items[] = [];
  for (let index = 0; index < items.length; index += 7) {
    weeks.push(items.slice(index, index + 7));
  }
  return weeks;
});

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

function formatDayLabel(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

function heatmapClass(intensity: number) {
  return `heatmap-cell--level-${Math.max(0, Math.min(intensity, 4))}`;
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

      <view class="panel" v-if="overview.badges.length">
        <text class="panel__title">已解锁勋章</text>
        <text class="panel__body">
          这些勋章会随着你的答题行为持续增长，后续会扩展更多成长触发规则。
        </text>
        <view class="badge-grid">
          <view
            v-for="item in overview.badges"
            :key="item.badge_key"
            class="badge-card"
          >
            <text class="badge-card__emoji">{{ item.emoji }}</text>
            <text class="badge-card__name">{{ item.name }}</text>
            <text class="badge-card__time">{{ formatTime(item.unlocked_at) }}</text>
          </view>
        </view>
      </view>

      <view class="panel" v-if="overview.calendar_heatmap.length">
        <text class="panel__title">近30天心动轨迹</text>
        <text class="panel__body">
          每完成一次测试，这里都会留下当天的活跃印记。颜色越深，代表当天互动越频繁。
        </text>
        <view class="heatmap">
          <view
            v-for="(week, weekIndex) in calendarHeatmapWeeks"
            :key="`week-${weekIndex}`"
            class="heatmap__week"
          >
            <view
              v-for="item in week"
              :key="item.date"
              class="heatmap-cell"
              :class="heatmapClass(item.intensity)"
            >
              <text class="heatmap-cell__day">{{ formatDayLabel(item.date) }}</text>
              <text class="heatmap-cell__count">
                {{ item.activity_count > 0 ? item.activity_count : "-" }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <view class="panel" v-if="overview.fragment_progress.length">
        <text class="panel__title">灵魂碎片进度</text>
        <text class="panel__body">
          不同测试会点亮不同的内在切面。你收集到的碎片越多，个人中心就越像一张更完整的自我地图。
        </text>
        <view class="rows rows--soft">
          <view
            v-for="item in overview.fragment_progress"
            :key="item.category_code"
            class="row row--soft"
          >
            <text class="row__name">
              {{ item.category_name }}{{ item.completed ? " · 已点亮" : "" }}
            </text>
            <text class="row__value">{{ item.unlocked_count }}/{{ item.total_count }}</text>
          </view>
        </view>
      </view>

      <view class="panel" v-if="overview.soul_fragments.length">
        <text class="panel__title">已收集的灵魂碎片</text>
        <text class="panel__body">
          每一片都代表一次更靠近自己的探索，后续这里会继续扩展成更完整的成长资产页。
        </text>
        <view class="fragment-grid">
          <view
            v-for="item in overview.soul_fragments"
            :key="item.fragment_key"
            class="fragment-card"
          >
            <text class="fragment-card__emoji">{{ item.emoji || "✨" }}</text>
            <text class="fragment-card__name">{{ item.name }}</text>
            <text class="fragment-card__category">{{ item.category }}</text>
            <text class="fragment-card__body">
              {{ item.insight || "这片碎片已经被点亮，说明你又看见了自己的一个切面。" }}
            </text>
          </view>
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

.badge-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.badge-card {
  padding: 18rpx;
  border-radius: 18rpx;
  background: rgba(255, 248, 238, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.12);
}

.badge-card__emoji {
  display: block;
  font-size: 34rpx;
}

.badge-card__name {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  font-weight: 600;
}

.badge-card__time {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.fragment-grid {
  margin-top: 18rpx;
  display: grid;
  gap: 14rpx;
}

.fragment-card {
  padding: 20rpx;
  border-radius: 20rpx;
  background:
    linear-gradient(145deg, rgba(255, 247, 235, 0.96), rgba(255, 235, 214, 0.92));
  border: 2rpx solid rgba(217, 111, 61, 0.12);
}

.fragment-card__emoji {
  display: block;
  font-size: 34rpx;
}

.fragment-card__name {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 600;
}

.fragment-card__category {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-accent;
}

.fragment-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.heatmap {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.heatmap__week {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10rpx;
}

.heatmap-cell {
  min-height: 92rpx;
  padding: 12rpx 10rpx;
  border-radius: 16rpx;
  border: 2rpx solid rgba(217, 111, 61, 0.08);
  background: rgba(255, 250, 244, 0.72);
}

.heatmap-cell--level-0 {
  background: rgba(255, 250, 244, 0.72);
}

.heatmap-cell--level-1 {
  background: rgba(255, 234, 214, 0.96);
}

.heatmap-cell--level-2 {
  background: rgba(246, 200, 163, 0.96);
}

.heatmap-cell--level-3 {
  background: rgba(230, 153, 101, 0.94);
}

.heatmap-cell--level-4 {
  background: rgba(191, 83, 33, 0.92);
}

.heatmap-cell__day,
.heatmap-cell__count {
  display: block;
  text-align: center;
}

.heatmap-cell__day {
  font-size: 18rpx;
  color: rgba(43, 33, 24, 0.72);
}

.heatmap-cell__count {
  margin-top: 10rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
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

.rows--soft {
  margin-top: 16rpx;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 250, 244, 0.92);
}

.row--soft {
  background: rgba(255, 247, 238, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
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
