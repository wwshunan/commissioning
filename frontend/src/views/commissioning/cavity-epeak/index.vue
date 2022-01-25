<template>
  <el-container>
    <el-header>
      <h3>上传腔体Epeak上限值</h3>
    </el-header>
    <el-main>
      <el-upload
          class="upload-demo"
          :action="upload_url"
          :limit="1"
          :on-success="success_handler"
          :on-error="error_handler"
      >
        <el-button size="small" type="primary">点击上传</el-button>
        <div slot="tip" class="el-upload__tip">上传腔压上限值文件</div>
      </el-upload>
    </el-main>
  </el-container>
</template>

<script>
export default {
  data() {
    return {
      upload_url: 'http://127.0.0.1:5000/commissioning/cavity-epk',
    }
  },
  methods: {
    success_handler() {
      this.$toast.success({
        title: '腔体Epeak文件上传',
        message: '上传成功！'
      })
    },
    error_handler() {
      this.$toast.error({
        title: '腔体Epeak文件上传',
        message: '上传失败！'
      })
    },
  }
}
</script>

<style scoped>
</style>