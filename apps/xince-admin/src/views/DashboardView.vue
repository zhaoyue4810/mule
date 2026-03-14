<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { getAdminAiMetrics, getAdminAiOverview, listAdminTests } from "@/services/admin";

const loading = ref(false);
const activeBucket = ref<"day" | "week" | "month">("day");
const overview = ref<any | null>(null);
const metrics = ref<any | null>(null);
const tests = ref<any[]>([]);

const seriesRows = computed(() => metrics.value?.series || []);
const chartMax = computed(() => {
  const rows = seriesRows.value;
  if (!rows.length) {
    return 1;
  }
  return Math.max(
    1,
    ...rows.map((item: any) => Math.max(item.total || 0, item.completed || 0, item.failed || 0)),
  );
});

const chartDots = computed(() => {
  const rows = seriesRows.value;
  const width = 100;
  const height = 50;
  const yBase = 45;
  if (!rows.length) {
    return [];
  }
  return rows.map((item: any, index: number) => {
    const x = rows.length === 1 ? width / 2 : (index / (rows.length - 1)) * width;
    const totalY = yBase - ((item.total || 0) / chartMax.value) * height;
    const completedY = yBase - ((item.completed || 0) / chartMax.value) * height;
    const failedY = yBase - ((item.failed || 0) / chartMax.value) * height;
    return {
      bucket: item.bucket,
      x,
      totalY,
      completedY,
      failedY,
      total: item.total || 0,
      completed: item.completed || 0,
      failed: item.failed || 0,
    };
  });
});

const totalLine = computed(() =>
  chartDots.value.map((item: { x: number; totalY: number }) => `${item.x},${item.totalY}`).join(" "),
);
const completedLine = computed(() =>
  chartDots.value
    .map((item: { x: number; completedY: number }) => `${item.x},${item.completedY}`)
    .join(" "),
);
const failedLine = computed(() =>
  chartDots.value.map((item: { x: number; failedY: number }) => `${item.x},${item.failedY}`).join(" "),
);

const successRate = computed(() => ((metrics.value?.success_rate || 0) * 100).toFixed(1));
const avgLatency = computed(() => Math.round(metrics.value?.avg_duration_ms || 0));
const calls24h = computed(() => metrics.value?.tasks_last_24h || 0);
const errors24h = computed(() => metrics.value?.failures_last_24h || 0);

async function loadDashboard() {
  loading.value = true;
  try {
    const [overviewPayload, metricsPayload, testsPayload] = await Promise.all([
      getAdminAiOverview(),
      getAdminAiMetrics(activeBucket.value),
      listAdminTests(),
    ]);
    overview.value = overviewPayload;
    metrics.value = metricsPayload;
    tests.value = testsPayload;
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "加载仪表盘数据失败");
  } finally {
    loading.value = false;
  }
}

onMounted(loadDashboard);
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <el-row :gutter="12">
      <el-col :span="6"><el-statistic title="AI 成功率" :value="Number(successRate)" suffix="%" /></el-col>
      <el-col :span="6"><el-statistic title="平均延迟" :value="avgLatency" suffix=" ms" /></el-col>
      <el-col :span="6"><el-statistic title="今日调用量" :value="calls24h" /></el-col>
      <el-col :span="6"><el-statistic title="今日失败量" :value="errors24h" /></el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="8">
        <el-card>
          <template #header>AI 概览</template>
          <div class="overview-grid">
            <div class="overview-item"><span>总任务</span><b>{{ overview?.total || 0 }}</b></div>
            <div class="overview-item"><span>等待中</span><b>{{ overview?.pending || 0 }}</b></div>
            <div class="overview-item"><span>运行中</span><b>{{ overview?.running || 0 }}</b></div>
            <div class="overview-item"><span>已完成</span><b>{{ overview?.completed || 0 }}</b></div>
            <div class="overview-item"><span>失败数</span><b>{{ overview?.failed || 0 }}</b></div>
            <div class="overview-item"><span>回退次数</span><b>{{ overview?.fallback_runs || 0 }}</b></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AI 指标趋势</span>
              <el-segmented
                v-model="activeBucket"
                :options="[
                  { label: '日', value: 'day' },
                  { label: '周', value: 'week' },
                  { label: '月', value: 'month' },
                ]"
                @change="loadDashboard"
              />
            </div>
          </template>
          <div v-if="chartDots.length" class="line-chart">
            <svg viewBox="0 0 100 50" preserveAspectRatio="none">
              <polyline class="line line--total" :points="totalLine" />
              <polyline class="line line--completed" :points="completedLine" />
              <polyline class="line line--failed" :points="failedLine" />
              <circle
                v-for="dot in chartDots"
                :key="`total-${dot.bucket}`"
                class="dot dot--total"
                :cx="dot.x"
                :cy="dot.totalY"
                r="0.7"
              />
            </svg>
            <div class="line-legend">
              <span><i class="legend-dot legend-dot--total" />总量</span>
              <span><i class="legend-dot legend-dot--completed" />完成</span>
              <span><i class="legend-dot legend-dot--failed" />失败</span>
            </div>
            <div class="bucket-row">
              <span v-for="dot in chartDots" :key="dot.bucket">{{ dot.bucket }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无趋势数据" />
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 16px">
      <template #header>测试列表</template>
      <el-table :data="tests">
        <el-table-column prop="test_code" label="编码" min-width="140" />
        <el-table-column prop="title" label="标题" min-width="240" />
        <el-table-column prop="category" label="分类" min-width="140" />
        <el-table-column label="匹配支持" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_match_enabled ? 'success' : 'info'">
              {{ row.is_match_enabled ? "是" : "否" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version_count" label="版本数" width="110" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard { display: block; }
.card-header { display:flex; justify-content:space-between; align-items:center; }
.overview-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.overview-item {
  border: 1px solid #efefef;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.overview-item span {
  color: #8a8f98;
  font-size: 13px;
}
.overview-item b {
  color: #2f3440;
  font-size: 16px;
}
.line-chart {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.line-chart svg {
  width: 100%;
  height: 220px;
  background: linear-gradient(180deg, #f9fafc 0%, #ffffff 100%);
  border-radius: 10px;
}
.line {
  fill: none;
  stroke-width: 0.55;
}
.line--total {
  stroke: #8f63ff;
}
.line--completed {
  stroke: #52c27f;
}
.line--failed {
  stroke: #f56c6c;
}
.dot--total {
  fill: #8f63ff;
}
.line-legend {
  display: flex;
  align-items: center;
  gap: 18px;
  color: #606266;
  font-size: 12px;
}
.line-legend span {
  display: flex;
  align-items: center;
}
.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
  display: inline-block;
}
.legend-dot--total {
  background: #8f63ff;
}
.legend-dot--completed {
  background: #52c27f;
}
.legend-dot--failed {
  background: #f56c6c;
}
.bucket-row {
  display: flex;
  justify-content: space-between;
  color: #8a8f98;
  font-size: 12px;
}
</style>
