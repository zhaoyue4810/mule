<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

import {
  approveImport,
  getImportPreview,
  listImportTasks,
  rejectImport,
  uploadImportFile,
} from "@/services/admin";

const loading = ref(false);
const uploadLoading = ref(false);
const tasks = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(10);
const previewVisible = ref(false);
const previewTask = ref<any | null>(null);
const previewPayload = ref<any | null>(null);

const statusTypeMap: Record<string, string> = {
  PENDING: "info",
  PARSING: "warning",
  PREVIEW: "warning",
  APPROVED: "success",
  REJECTED: "danger",
  FAILED: "",
};

async function loadTasks() {
  loading.value = true;
  try {
    const payload = await listImportTasks(page.value, size.value);
    tasks.value = payload.items || [];
    total.value = payload.total || 0;
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "加载导入任务失败");
  } finally {
    loading.value = false;
  }
}

async function handleFileUpload(file: File) {
  uploadLoading.value = true;
  try {
    await uploadImportFile(file);
    ElMessage.success("文件上传并解析成功");
    await loadTasks();
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "上传失败");
  } finally {
    uploadLoading.value = false;
  }
  return false;
}

async function openPreview(task: any) {
  previewTask.value = task;
  previewVisible.value = true;
  previewPayload.value = null;
  try {
    previewPayload.value = await getImportPreview(task.id);
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "预览加载失败");
  }
}

async function handleApprove(task: any) {
  try {
    await approveImport(task.id);
    ElMessage.success("导入任务已通过");
    await loadTasks();
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "审核失败");
  }
}

async function handleReject(task: any) {
  try {
    const reason = await ElMessageBox.prompt("请输入拒绝原因", "拒绝导入", {
      confirmButtonText: "确认拒绝",
      cancelButtonText: "取消",
      inputPlaceholder: "例如：结构不完整，需重新导出",
    });
    await rejectImport(task.id, reason.value || "");
    ElMessage.success("导入任务已拒绝");
    await loadTasks();
  } catch (err) {
    if ((err as any)?.message === "cancel") {
      return;
    }
    ElMessage.error(err instanceof Error ? err.message : "拒绝失败");
  }
}

onMounted(loadTasks);
</script>

<template>
  <el-card>
    <template #header>
      <div class="header">
        <span>内容导入工作流</span>
        <el-upload
          :show-file-list="false"
          :before-upload="handleFileUpload"
          accept=".docx,.html"
        >
          <el-button type="primary" :loading="uploadLoading">上传 docx/html</el-button>
        </el-upload>
      </div>
    </template>

    <el-table :data="tasks" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="file_name" label="文件名" min-width="220" />
      <el-table-column prop="file_type" label="类型" width="90" />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusTypeMap[row.status] || 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="操作时间" width="190" />
      <el-table-column prop="operator_name" label="操作人" width="110" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openPreview(row)">查看</el-button>
          <el-button link type="success" @click="handleApprove(row)">通过</el-button>
          <el-button link type="danger" @click="handleReject(row)">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadTasks"
      />
    </div>
  </el-card>

  <el-dialog v-model="previewVisible" title="导入预览" width="860px">
    <template v-if="previewPayload?.preview_json">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务 ID">{{ previewPayload.id }}</el-descriptions-item>
        <el-descriptions-item label="文件类型">{{ previewPayload.file_type }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ previewPayload.status }}</el-descriptions-item>
        <el-descriptions-item label="解析日志">{{ previewPayload.parse_log || "-" }}</el-descriptions-item>
      </el-descriptions>
      <el-divider />
      <pre class="json-preview">{{ JSON.stringify(previewPayload.preview_json, null, 2) }}</pre>
    </template>
    <el-empty v-else description="暂无预览数据" />
  </el-dialog>
</template>

<style scoped>
.header { display:flex; align-items:center; justify-content:space-between; }
.pager { margin-top: 16px; display:flex; justify-content:flex-end; }
.json-preview {
  max-height: 420px;
  overflow: auto;
  border-radius: 8px;
  background: #f8f8f8;
  padding: 12px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
