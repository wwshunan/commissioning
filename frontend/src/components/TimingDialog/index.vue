<template>
<el-dialog title="定时参数" :visible.sync="dialogFormVisible">
  <el-form :model="form">
    <el-form-item label="重复频率" :label-width="formLabelWidth">
      <el-input v-model="form.repeat" autocomplete="off"></el-input>
    </el-form-item>
	<el-form-item label="脉宽" :label-width="formLabelWidth">
      <el-input v-model="form.width" autocomplete="off"></el-input>
    </el-form-item>
  </el-form>
  <div slot="footer" class="dialog-footer">
    <el-button @click="dialogFormVisible = false">取 消</el-button>
    <el-button type="primary" @click="send_data">确 定</el-button>
  </div>
</el-dialog>
</template>

<script>
export default {
  name: 'TimingDialog',
  data() {
    return {
      dialogFormVisible: false,
      formLabelWidth: '120px',
      form: {
        repeat: 1,
        width: 300
      }
    }
  },
  methods: {
    show() {
      this.dialogFormVisible = true
    },
	send_data() {
	  this.dialogFormVisible = false
	  this.$emit('timing-msg', this.form.repeat,  this.form.width)
	}
  }
}
</script>