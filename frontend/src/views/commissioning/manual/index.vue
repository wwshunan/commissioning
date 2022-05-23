<template>
  <el-container>
    <el-header>
      <h3>说明文档</h3>
    </el-header>
    <el-main>
      <div v-html="markdownToHtml" align="left"></div>
    </el-main>
  </el-container>
</template>

<script>
import { marked } from 'marked'
import request from '@/utils/request'

export default {
  data() {
    return {
      manual: ''
    }
  },
  computed: {
    markdownToHtml() {
      return marked(this.manual)
    }
  },
  methods: {
    async get_manual() {
      let response = await request({
        url: '/commissioning/get-manual',
        method: 'get',
      })
      this.manual = response["data"];
      console.log(this.manual)
    }
  },
  async mounted() {
    await this.get_manual()
  }
}
</script>

<style scoped>
</style>