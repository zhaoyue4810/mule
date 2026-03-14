<script setup lang="ts">
import { onMounted, ref } from "vue";
import { listAdminTests } from "@/services/admin";

const tests = ref<any[]>([]);
onMounted(async () => {
  tests.value = await listAdminTests();
});
</script>

<template>
  <el-card>
    <template #header>测试管理</template>
    <el-table :data="tests">
      <el-table-column prop="test_code" label="编码" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="category" label="分类" />
      <el-table-column prop="version_count" label="版本数" />
    </el-table>
  </el-card>
</template>
