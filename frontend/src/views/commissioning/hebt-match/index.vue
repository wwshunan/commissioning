<template>
  <el-container>
    <el-header>
      <h3>HEBT匹配</h3>
    </el-header>
    <el-main>
      <el-row :gutter="40">
        <el-col :span="18">
          <h4>四极铁和校正铁参数优化</h4>
          <el-form ref="form" :model="form" size="mini">
            <el-row :gutter="40">
              <el-col :span="12">
                <el-form-item label="最大迭代次数">
                  <el-col :span="8">
                    <el-input v-model="max_iter"></el-input>
                  </el-col>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="迭代步长">
                  <el-col :span="8">
                    <el-input v-model="step"></el-input>
                  </el-col>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="40">
              <el-col :span="12">
                <el-form-item label="频率 [Hz]">
                  <el-col :span="8">
                    <el-input v-model="freq"></el-input>
                  </el-col>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="流强抽样次数">
                  <el-col :span="8">
                    <el-input v-model="sample_num"></el-input>
                  </el-col>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="40">
              <el-col :span="12">
                <el-form-item label="SSFC电流修正因子">
                  <el-col :span="8">
                    <el-input v-model="ssfc_modify_factor"></el-input>
                  </el-col>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="SSFC截止流强 [uA]">
                  <el-col :span="8">
                    <el-input v-model="ssfc_stop_current"></el-input>
                  </el-col>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row>
              <el-col :span="12">
                <el-form-item label="优化参数">
                  <el-col :span="8">
                    <el-select v-model="opti_param">
                      <el-option v-for="item in opti_param_options" :key="item.text" :label="item.text" :value="item.value">
                      </el-option>
                    </el-select>
                  </el-col>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="优化目标">
                  <el-col :span="8">
                    <el-select v-model="target">
                      <el-option v-for="item in target_options" :key="item.text" :label="item.text" :value="item.value">
                      </el-option>
                    </el-select>
                  </el-col>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item style="text-align: right">
              <el-row>
                <el-col :span="5">
                  <el-button type="primary" plain @click="start_match">开始</el-button>
                </el-col>
                <el-col :span="5">
                  <el-button type="danger" @click="cancel_match">停止</el-button>
                </el-col>
              </el-row>
            </el-form-item>
          </el-form>
          <div style="text-align: left; font-weight: bold">优化结果输出</div>
          <el-table v-if="opti_param==='quad'" :data="currents" ref="table" highlight-current-row max-height="700px">
            <el-table-column prop="index" label="序号">
            </el-table-column>
            <el-table-column prop="t0q01" label="T0-Q01">
            </el-table-column>
            <el-table-column prop="t0q02" label="T0-Q02">
            </el-table-column>
            <el-table-column prop="t0d01" label="T0-D01">
            </el-table-column>
            <el-table-column prop="t2q01" label="T2-Q01">
            </el-table-column>
            <el-table-column prop="t2d01" label="T2-D01">
            </el-table-column>
            <el-table-column prop="t2q02" label="T2-Q02">
            </el-table-column>
            <el-table-column prop="t2q03" label="T2-Q03">
            </el-table-column>
            <el-table-column prop="t2q04" label="T2-Q04">
            </el-table-column>
            <el-table-column prop="t2ch03" label="T2-CH03">
            </el-table-column>
            <el-table-column prop="t2cv03" label="T2-CV03">
            </el-table-column>
            <el-table-column prop="target" label="TARGET">
            </el-table-column>
          </el-table>
          <el-table v-else :data="currents" ref="table" highlight-current-row max-height="700px">
            <el-table-column prop="index" label="序号">
            </el-table-column>
            <el-table-column prop="t0ch01" label="T0-CH01">
            </el-table-column>
            <el-table-column prop="t0cv01" label="T0-CV01">
            </el-table-column>
            <el-table-column prop="t2ch01" label="T2-CH01">
            </el-table-column>
            <el-table-column prop="t2cv01" label="T2-CV01">
            </el-table-column>
            <el-table-column prop="t2ch02" label="T2-CH02">
            </el-table-column>
            <el-table-column prop="t2cv02" label="T2-CV02">
            </el-table-column>
            <el-table-column prop="t2ch03" label="T2-CH03">
            </el-table-column>
            <el-table-column prop="t2cv03" label="T2-CV03">
            </el-table-column>
            <el-table-column prop="target" label="TARGET">
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script>
import request from '@/utils/request'
import { Message } from 'element-ui'


export default {
  data() {
    return {
      max_iter: 50,
      step: 2,
      freq: 30,
      ssfc_stop_current: 30,
      ssfc_modify_factor: 2,
      sample_num: 100,
      opti_param: "quad",
      opti_param_options: [
        {value: "quad", text: "quad"},
        {value: "steer", text: "steer"},
      ],
      target: "SSFC - Halo Max",
      target_options: [
        {value: "T2FC Max", text: "Mode 1: T2FC Max"},
        {value: "SSFC Max", text: "Mode 2: SSFC Max"},
        {value: "Halo Min", text: "Mode 3: Halo Min"},
        {value: "SSFC - Halo Max", text: "Mode 4: SSFC - Halo Max"},
      ],
      task_id: 0,
      currents: []
    }
  },
  methods: {
    async start_match() {
      const path = '/commissioning/hebt-match/matching';
      const res = await request({
        url: path,
        data: {
          target: this.target,
          opti_param: this.opti_param,
          sample_num: this.sample_num,
          step: this.step,
          max_iter: this.max_iter,
          freq: this.freq,
          ssfc_stop_current: this.ssfc_stop_current,
          ssfc_modify_factor: this.ssfc_modify_factor
        },
        method: 'post',
      })
      this.task_id = res.task_id
      await this.get_status(res.task_id)
    },
    async get_status(task_id) {
      const path = `/commissioning/hebt-match/${task_id}`;
      try {
        const res = await request({
          url: path,
          method: 'get'
        })
        const taskStatus = res.data.task_status;
        Message({
          message: res.data.task_status,
          type: 'info',
          duration: 3 * 1000
        })
        if (taskStatus === 'finished') {
          this.currents = res.data.task_result
        }

        if (taskStatus === 'finished' || taskStatus === 'failed') return false;
        setTimeout(async () => {
          await this.get_status(res.data.task_id);
        }, 5000);
      } catch (e) {
        console.log(e)
      }
    },
    async cancel_match() {
      const path = `/commissioning/hebt-match/cancel/${this.task_id}`;
      try {
        const res = await request({
          url: path,
          method: 'post'
        })
      } catch (e) {
        console.log(e)
      }
    },
  }
}
</script>

<style scoped>
</style>