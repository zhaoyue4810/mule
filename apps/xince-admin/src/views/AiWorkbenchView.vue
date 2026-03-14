<script setup lang="ts">
import { onMounted, ref } from "vue";

import {
  getAdminAiMetrics,
  getAdminAiOverview,
  getAdminAiTaskDetail,
  getAdminPromptCompare,
  getAdminPromptHistory,
  listAdminAiTasks,
  listAdminPromptTemplates,
  retryAdminAiFailed,
  retryAdminAiTask,
} from "@/services/admin";

type AiTaskRow = { id: number };
type PromptRow = { id: number };

const overview = ref<any | null>(null);
const metrics = ref<any | null>(null);
const tasks = ref<any[]>([]);
const prompts = ref<any[]>([]);
const selectedTask = ref<any | null>(null);
const selectedPromptHistory = ref<any[]>([]);
const selectedPromptCompare = ref<any | null>(null);
const activeBucket = ref("day");

async function loadAll() {
  overview.value = await getAdminAiOverview();
  metrics.value = await getAdminAiMetrics(activeBucket.value);
  tasks.value = (await listAdminAiTasks()).items;
  prompts.value = await listAdminPromptTemplates();
}

async function inspectTask(taskId: number) {
  selectedTask.value = await getAdminAiTaskDetail(taskId);
}

async function inspectPrompt(templateId: number) {
  selectedPromptHistory.value = await getAdminPromptHistory(templateId);
  selectedPromptCompare.value = await getAdminPromptCompare(templateId);
}

async function retryTask(taskId: number) {
  await retryAdminAiTask(taskId);
  await loadAll();
}

async function retryFailed() {
  await retryAdminAiFailed();
  await loadAll();
}

onMounted(() => {
  void loadAll();
});
</script>

<template>
  <div class="workbench">
    <el-row :gutter="16">
      <el-col :span="8"><el-card><template #header>任务概览</template><pre>{{ overview }}</pre></el-card></el-col>
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="header-row">
              <span>指标面板</span>
              <div>
                <el-segmented v-model="activeBucket" :options="['day', 'week', 'month']" @change="loadAll" />
                <el-button type="primary" style="margin-left: 12px" @click="retryFailed">批量重试失败任务</el-button>
              </div>
            </div>
          </template>
          <pre>{{ metrics }}</pre>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="14">
        <el-card>
          <template #header>任务列表</template>
          <el-table :data="tasks" @row-click="(row: AiTaskRow) => inspectTask(row.id)">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="status" label="状态" width="120" />
            <el-table-column prop="provider" label="供应商" width="120" />
            <el-table-column prop="duration_ms" label="耗时(ms)" width="120" />
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button link type="primary" @click.stop="retryTask(scope.row.id)">重试</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <template #header>任务详情</template>
          <pre>{{ selectedTask }}</pre>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>Prompt 模板</template>
          <el-table :data="prompts" @row-click="(row: PromptRow) => inspectPrompt(row.id)">
            <el-table-column prop="template_code" label="模板编码" />
            <el-table-column prop="scene" label="场景" width="120" />
            <el-table-column prop="version" label="版本" width="80" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>版本对比 / 历史</template>
          <pre>{{ selectedPromptCompare }}</pre>
          <el-divider />
          <pre>{{ selectedPromptHistory }}</pre>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.workbench { display:flex; flex-direction:column; }
.header-row { display:flex; justify-content:space-between; align-items:center; }
</style>
