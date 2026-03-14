<script setup lang="ts">
import { onMounted, ref } from "vue";

import { getAdminAiMetrics, getAdminAiOverview, listAdminTests } from "@/services/admin";

const overview = ref<any | null>(null);
const metrics = ref<any | null>(null);
const tests = ref<any[]>([]);

onMounted(async () => {
  overview.value = await getAdminAiOverview();
  metrics.value = await getAdminAiMetrics();
  tests.value = await listAdminTests();
});
</script>

<template>
  <div class="grid">
    <el-card><template #header>AI 总览</template><pre>{{ overview }}</pre></el-card>
    <el-card><template #header>AI 指标</template><pre>{{ metrics }}</pre></el-card>
    <el-card><template #header>测试概览</template><el-table :data="tests"><el-table-column prop="test_code" label="编码" /><el-table-column prop="title" label="标题" /><el-table-column prop="category" label="分类" /></el-table></el-card>
  </div>
</template>

<style scoped>
.grid { display:grid; gap:16px; }
</style>
