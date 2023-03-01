<template>
  <el-container>
    <el-header>
      <h3>扫相</h3>
    </el-header>
    <el-main>
      <el-row :gutter="40">
        <el-col :span="8">
          <el-form @submit.prevent="onSubmit" enctype="multipart/form-data" size="mini">
            <el-form-item>
              <div style="text-align: left; font-weight: bold">阈值设定</div>
              <el-row :gutter="10">
                <el-col :span="5">
                  <span>轨道小于</span>
                </el-col>
                <el-col :span="6">
                  <el-input v-model="orbit_offset_limit" @keyup.enter.native="setBpmSumAndOrbitLimit"></el-input>
                </el-col>
                <el-col :span="5">
                  <span>BPM2 SUM大于</span>
                </el-col>
                <el-col :span="6">
                  <el-input v-model="bpm_sum_limit" @keyup.enter.native="setBpmSumAndOrbitLimit"></el-input>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item label="扫相模式">
              <el-radio-group v-model="selected">
                <el-radio v-for="item in options" :label="item.value" :key="item.value">
                  {{item.name}}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="BPM个数">
              <el-radio-group v-model="bpm_mode_selected" @change="reset_bpm">
                <el-radio v-for="item in bpm_mode_options" :label="item.value" :key="item.value">
                  {{item.name}}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="BPM频率" v-if="bpm_mode_selected === 'single'">
              <el-radio-group v-model="bpm_harm_selected">
                <el-radio v-for="item in bpm_harm_options" :label="item.value" :key="item.value">
                  {{item.name}}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="粒子种类">
              <el-select v-model="particle_type">
                <el-option v-for="item in particle_options" :key="item.text" :label="item.text" :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="入口全能量[MeV]">
              <el-col :span="8">
                <el-input v-model="in_energy"></el-input>
              </el-col>
            </el-form-item>
            <el-form-item label="腔体序号">
              <el-col :span="12">
                <el-select v-model="cavity_name" @change="init_bpm_and_amp">
                  <el-option v-for="item in cavity_options" :key="item.name" :label="item.name" :value="item.value">
                  </el-option>
                </el-select>
              </el-col>
              <el-col :span="8">
                <el-select v-model="bpm_select" v-if="bpm_mode_selected === 'single'">
                  <el-option v-for="item in bpm_options" :key="item.name" :label="item.name" :value="item.value">
                  </el-option>
                </el-select>
              </el-col>
            </el-form-item>
            <el-form-item>
              <el-row :gutter="10">
                <el-col :span="8">
                  <el-input v-model="start_phase"></el-input>
                </el-col>
                <el-col :span="8">
                  <el-input v-model="current_phase"></el-input>
                </el-col>
                <el-col :span="8">
                  <el-input v-model="stop_phase"></el-input>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item label="相位步长[deg]">
              <el-col :span="8">
                <el-input v-model="scan_step"></el-input>
              </el-col>
            </el-form-item>
            <el-form-item label="相位设置后等待[s]">
              <el-col :span="8">
                <el-input v-model="cavity_res_time"></el-input>
              </el-col>
            </el-form-item>
            <el-form-item>
              <div style="text-align: right; font-weight: bold">Bpm读取N次, 读取间隔dT秒</div>
              <el-row>
                <el-col :span="12">
                  <el-row :gutter="2">
                    <el-col :span="6" style="text-align: right">N</el-col>
                    <el-col :span="18">
                      <el-input v-model="bpm_read_num"></el-input>
                    </el-col>
                  </el-row>
                </el-col>
                <el-col :span="12">
                  <el-row :gutter="5">
                    <el-col :span="6" style="text-align: right">dT</el-col>
                    <el-col :span="18">
                      <el-input v-model="bpm_read_sep"></el-input>
                    </el-col>
                  </el-row>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item label="设置腔体相位">
              <el-col :span="8">
                <el-input v-model="synchPhase" @keyup.enter.native="setSynchPhase"></el-input>
              </el-col>
            </el-form-item>
            <el-form-item>
              <div style="text-align: left; font-weight: bold">当前扫相腔体状态</div>
              <el-row :gutter="10" align="middle" type="flex">
                <el-col :span="6">
                  <el-form-item label="Epk上限">
                    <el-input v-model="amp_limit"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="Epk">
                    <el-input v-model="amp"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="6">
                  <el-form-item label="相位">
                    <el-input v-model="phase"></el-input>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item>
              <div style="text-align: left; font-weight: bold">读取腔后BPM相位</div>
              <el-row align="center">
                <el-col :span="12">
                  <label>{{ bpm_name }}</label>
                </el-col>
                <el-col :span="6">
                  <label style="color: red">{{ bpm_phase }}</label>
                </el-col>
                <el-col :span="6">
                  <el-button type="primary" @click="readBpmPhase">读取</el-button>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item>
              <el-row align="center">
                <el-col :span="12">
                  <label>选择腔体</label>
                </el-col>
                <el-col :span="6">
                  <el-button disabled>
                    <i class="fa fa-angle-double-left"></i>
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button @click.native="config_next_cavity">
                    <i class="fa fa-angle-double-right"></i>
                  </el-button>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item>
              <el-row type="flex" justify="end">
                <el-col :span="5">
                  <el-button type="primary" @click="start_scan" :disabled="scan_disabled">开始</el-button>
                </el-col>
                <el-col :span="5">
                  <el-button type="warning" @click="onPause">{{ pause_text }}</el-button>
                </el-col>
                <el-col :span="5">
                  <el-button type="danger" @click="stop=true">停止</el-button>
                </el-col>
              </el-row>
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="16">
          <div ref="chart"></div>
          <div class="scrollable">
            <fit-report v-for="(record, i) in fit_records" :key="record.cavity_name + i"
              :cavity_name="record.cavity_name" :fit_entr_phase="record.entr_phase" :fit_phase="record.phase" 
              :fit_amp="record.amp" :fit_energy="record.energy">
            </fit-report>
          </div>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script>
import { Message } from 'element-ui'
import request from '@/utils/request'

import Plotly from 'plotly.js-dist-min'
import FitReport from "@/components/FitReport/index"

var fit_icon = {
  'width': 500,
  'height': 600,
  'path': "M64 400C64 408.8 71.16 416 80 416H480C497.7 416 512 430.3 512 448C512 465.7 497.7 480 480 480H80C35.82 480 0 444.2 0 400V64C0 46.33 14.33 32 32 32C49.67 32 64 46.33 64 64V400zM342.6 278.6C330.1 291.1 309.9 291.1 297.4 278.6L240 221.3L150.6 310.6C138.1 323.1 117.9 323.1 105.4 310.6C92.88 298.1 92.88 277.9 105.4 265.4L217.4 153.4C229.9 140.9 250.1 140.9 262.6 153.4L320 210.7L425.4 105.4C437.9 92.88 458.1 92.88 470.6 105.4C483.1 117.9 483.1 138.1 470.6 150.6L342.6 278.6z" 
}

var down_icon = {
  'width': 500,
  'height': 600,
  'path': "M374.6 310.6l-160 160C208.4 476.9 200.2 480 192 480s-16.38-3.125-22.62-9.375l-160-160c-12.5-12.5-12.5-32.75 0-45.25s32.75-12.5 45.25 0L160 370.8V64c0-17.69 14.33-31.1 31.1-31.1S224 46.31 224 64v306.8l105.4-105.4c12.5-12.5 32.75-12.5 45.25 0S387.1 298.1 374.6 310.6z" 
}

var up_icon = {
  'width': 500,
  'height': 600,
  'path': "M374.6 246.6C368.4 252.9 360.2 256 352 256s-16.38-3.125-22.62-9.375L224 141.3V448c0 17.69-14.33 31.1-31.1 31.1S160 465.7 160 448V141.3L54.63 246.6c-12.5 12.5-32.75 12.5-45.25 0s-12.5-32.75 0-45.25l160-160c12.5-12.5 32.75-12.5 45.25 0l160 160C387.1 213.9 387.1 234.1 374.6 246.6z" 
}

var del_icon = {
  'width': 500,
  'height': 600,
  'path': "M310.6 361.4c12.5 12.5 12.5 32.75 0 45.25C304.4 412.9 296.2 416 288 416s-16.38-3.125-22.62-9.375L160 301.3L54.63 406.6C48.38 412.9 40.19 416 32 416S15.63 412.9 9.375 406.6c-12.5-12.5-12.5-32.75 0-45.25l105.4-105.4L9.375 150.6c-12.5-12.5-12.5-32.75 0-45.25s32.75-12.5 45.25 0L160 210.8l105.4-105.4c12.5-12.5 32.75-12.5 45.25 0s12.5 32.75 0 45.25l-105.4 105.4L310.6 361.4z" 
}

function make_watch_func(var_name) {
  return function(new_value) {
    this.$storage.set(var_name, new_value)
  }
}

function make_watch_dict(var_names) {
  let watch_dict = {}
  for (let name of var_names) {
    watch_dict[name] = make_watch_func(name)
  }
  return watch_dict
}

function restore_params(watch_dict, context) {
    for (const [key, value] of Object.entries(watch_dict)) {
      context[key] = context.$storage.get(key, value)
    }
}

const particle_data = {
  "Proton": {
    "mass": 938.272083,
    "charge": 1
  },
  "36Ar12+": {
    "mass": 33532.53,
    "charge": 12
  },
  "40Ar13+": {
    "mass": 37245.6,
    "charge": 13
  },
  "40Ca13+": {
    "mass": 37218.2748,
    "charge": 13
  },
  "55Mn17+": {
    "mass": 51165.778,
    "charge": 17
  },
}
export default {
  components: {
    FitReport
  },
  data() {
    return {
      particle_type: "Proton",
      particle_options: [
        {value: "Proton", text: "Proton"},
        {value: "36Ar12+", text: "36Ar12+"},
        {value: "40Ar13+", text: "40Ar13+"},
        {value: "40Ca13+", text: "40Ca13+"},
        {value: "55Mn17+", text: "55Mn17+"},
      ],
      in_energy: 4,
      orbit_offset_limit: 5,
      bpm_sum_limit: 1000,
      cavity_name: '',
      cavity_options: [],
      bpm_select: '',
      bpm_options: [],
      cavity_infos: {},
      start_phase: -178,
      current_phase: -178,
      stop_phase: 180,
      scan_step: 15,
      cavity_res_time: 2,
      bpm_read_num: 4,
      bpm_read_sep: 1,
      options: [
        {value: 'manual', name: '人工扫相'},
        {value: 'auto', name: '自动扫相'}
      ],
      bpm_mode_options: [
        {value: 'single', name: '单BPM'},
        {value: 'double', name: '双BPM'}
      ],
      bpm_harm_options: [
        {value: 'single', name: '基频'},
        {value: 'double', name: '二倍频'}
      ],
      selected: 'manual',
      bpm_mode_selected: 'double',
      bpm_harm_selected: 'double',
      amp_limit_file: null,
      amp_limit: 0,
      amp: 0,
      phase: 0,
      synchPhase: 0,
      lattice: {},
      stop: false,
      bpm_name: '',
      bpm_phase: 0,
      pause: false,
      pause_text: '暂停',
      monitor: true,
      ready: false,
      scan_unready: false,
      scan_disabled: false,
      fit_records: [],
      coordRange: {},
      fail_times: 0,
      selected_points: [],
      chart_data:[
        {
          x: [],
          y: [],
          mode: 'lines+markers'
        },
        {
          x: [],
          y: [],
          mode: 'lines+markers'
        },
        {
          name: 'curve fit',
          x: [],
          y: [],
          mode: 'lines+markers'
        },
        {
          x: [],
          y: [],
          mode: 'lines+markers'
        },

      ],
      layout: {
        title: "腔体相位 vs BPM相位",
        xaxis: {
          title: {
            text: "腔体相位 [deg]"
          }
        },
        yaxis: {
          title: {
            text: "BPM相位 [deg]"
          }
        }
      },
      config: {
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d'],
        modeBarButtonsToAdd: [
          {
            name: '拟合',
            icon: fit_icon,
            click: async (gd) => { 
              let res = await this.curve_fit()
            }
          },
          {
            name: '减360度',
            icon: down_icon,
            click: () => {
              this.manipulate_points('move_down')
            }
          },
          {
            name: '加360度',
            icon: up_icon,
            click: () => {
              this.manipulate_points('move_up')
            }
          },
          {
            name: '删除',
            icon: del_icon,
            click: () => {
              this.manipulate_points('delete')
            }
          },
        ],
        displaylogo: false
      }
    }
  },
  methods: {
    async setBpmSumAndOrbitLimit() {
      const path =  '/commissioning/phasescan/set-bpm-sum-offset-limit'
      await request({
        url: path,
        data: {
          bpm_sum_limit: this.bpm_sum_limit,
          orbit_offset_limit: this.orbit_offset_limit
        },
        method: 'post',
      })
    },
    reset_bpm() {
      if (this.bpm_mode_selected === 'double') {
        this.bpm_harm_selected = 'double'
        this.bpm_select = this.bpm_options[0].value
      }
    },
    async init_bpm_and_amp() {
      this.bpm_mode_selected = this.cavity_infos[this.cavity_name]['bpm_mode']
      this.bpm_options = ['bpm1_name', 'bpm2_name', 'bpm3_name'].map(e => {
        return {
          value: this.cavity_infos[this.cavity_name][e], 
          name: this.cavity_infos[this.cavity_name][e]
        }
      }) 
      this.bpm_select= this.bpm_options[0].name
      await this.init_pvs({
        cavity_name: this.cavity_name,
        bpm_mode: this.bpm_mode_selected
      })
      await this.get_amp()
    },
    async readBpmPhase() {
      const path = '/commissioning/phasescan/read-bpm-phase'
      const response = await request({
        url: path,
        method: 'get',
      })
      this.bpm_phase = response['bpm_phase']
      this.bpm_name = response['bpm_name']
    },
    async config_next_cavity() {
      this.in_energy = this.fit_records.slice(-1)[0]['energy']
      await this.setSynchPhase()
      let cavity_array = []
      this.cavity_options.forEach(e => {
        cavity_array.push(e.text)
      })
      const next_cavity_idx = cavity_array.indexOf(this.cavity_name) + 1
      this.cavity_name = cavity_array[next_cavity_idx]
      await this.init_bpm_and_amp()
    },
    async setSynchPhase() {
      this.lattice[this.cavity_name].phase = this.synchPhase
      this.lattice[this.cavity_name].amp = this.amp
      const path = '/commissioning/phasescan/synch-phase-set'
      const response = await request({
        url: path,
        data: {lattice: this.lattice},
        method: 'post',
      })
      Message({
        message: response.message,
        type: 'info',
        duration: 5 * 1000
      })
    },
    manipulate_points(kind) {
      let prev_point_index = this.selected_points.length 
      this.selected_points.reverse().forEach(p => {
        switch (kind) {
          case 'move_up': {
            this.chart_data[p.curveNumber]['y'][p.pointIndex] += 360
            break
          }
          case 'move_down': {
            this.chart_data[p.curveNumber]['y'][p.pointIndex] -= 360
            break
          }
          default: {
            if (p.pointIndex === prev_point_index) 
              break
            let series_array = [0, 1, 2]
            series_array.forEach(series_index => {
              if (this.chart_data[series_index].x.length !== 0) {
                this.chart_data[series_index].x.splice(p.pointIndex, 1)
                this.chart_data[series_index].y.splice(p.pointIndex, 1)
              }
            prev_point_index = p.pointIndex
            })
          }
        }
      })
      Plotly.redraw(this.$refs.chart)
    },
    async load_cavity_infos() {
      let response = await request({
        url: '/commissioning/phasescan/config',
        method: 'get',
      })
      this.cavity_infos = response["cavity_infos"];

      response = await request({
        url: '/commissioning/phasescan/read-lattice-cache',
        method: 'get',
      })

      for (let cavity_name in this.cavity_infos) {
        this.cavity_options.push({value: cavity_name, text: cavity_name})
        if (response['lattice']) {
          this.lattice[cavity_name] = response['lattice'][cavity_name]
        } else {
          this.lattice[cavity_name] = {
            'amp': 0,
            'phase': 0
          }
        }
      }
      const cavity_name = this.cavity_options[0].value
      let watch_dict = {
        'cavity_name': cavity_name,
        'selected': this.selected,
        'particle_type': this.particle_type,
        'in_energy': this.in_energy,
        'scan_step': this.scan_step,
        'cavity_res_time': this.cavity_res_time,
        'bpm_read_num': this.bpm_read_num,
        'bpm_read_sep': this.bpm_read_sep
      }
      restore_params(watch_dict, this)
      //if (this.$storage.has('cavity_name')) {
      //  this.cavity_name = this.$storage.get('cavity_name')
      //} else {
      //}
      //if (this.$storage.has('selected')) {
      //  this.selected = this.$storage.get('selected')
      //}
      //if (this.$storage.has('particle_type')) {
      //  this.particle_type = this.$storage.get('particle_type')
      //}
      this.bpm_mode_selected = this.cavity_infos[this.cavity_name]['bpm_mode']
    },
    async init_pvs(cavity_info) {
      const path = '/commissioning/phasescan/init-pvs';
      await request({
        url: path,
        data: cavity_info,
        method: 'post',
      })
    },

    async fetch_ready_status(path) {
      let res
      try {
        res = await request({
          url: path,
          method: 'get',
        })
        this.ready = true
      } catch (e) {
        this.ready = false
        res = e
      }
      //this.ready = response.ready
      if (!this.ready) {
        this.fail_times++
        if (this.fail_times === 3) this.scan_unready = true
      }
      return res
    },

    async start_monitor() {
      this.monitor = true
      const path = '/commissioning/phasescan/get-status'
      let res = await this.fetch_ready_status(path)
      let new_res
      let count = 0
      let timer = setInterval(async () => {
        new_res = await this.fetch_ready_status(path)
        if (new_res.message) {
          if ((new_res.message !== res.message) || (count % 5 === 0)) {
            Message({
              message: res.message || 'Error',
              type: 'error',
              duration: 5 * 1000
            })
          }
          count %= 5
          ++count
          res = new_res
        }
        if (!this.monitor) clearInterval(timer)
      }, 1000)
    },
    stop_monitor() {
      this.monitor = false
    },
    async start_scan() {
      this.scan_disabled = true
      let path = '/commissioning/phasescan/set-mode'
      await request({
        url: path,
        data: {'cavity_name': this.cavity_name},
        method: 'post'
      })


      let res

      if (this.selected === "manual")  {
        let exit_scan = await this.scan_per_cavity()
        if (exit_scan) {
          this.stop = false
        }
      }
      else {
        const sc_cavity_amp_tol = 0.5
        const rt_cavity_amp_tol = 1.0
        let cavity_array = []
        this.cavity_options.forEach(e => {
          cavity_array.push(e.text)
        })
        const start_cavity_idx = cavity_array.indexOf(this.cavity_name)
        let cavity_range = this.cavity_options.slice(start_cavity_idx)
        for (const cav of cavity_range) {
          let count = 0
          while (count < 3) {
            if (this.amp > this.amp_limit) {
              this.amp = this.amp_limit
              Message({
                message: "所需腔压超过Epeak阈值了",
                type: 'info',
                duration: 5 * 1000
              })
            }
            this.cavity_name = cav.value
            let exit_scan = await this.scan_per_cavity()
            if (exit_scan) {
              this.stop = false
              return
            }

            res = await this.curve_fit()
            this.in_energy = this.fit_records.slice(-1)[0]['energy']
            this.synchPhase = res.rf_phase.toFixed(1)
            path = '/commissioning/phasescan/calibrated-amp'
            try {
              res = await request({
                url: path,
                data: {
                  cavity_name: this.cavity_name,
                  amp: res.amp.toFixed(1)
                },
                method: 'post'
              })
              Message({
                message: res.message,
                type: 'success',
                duration: 5 * 1000
              })
            } catch (e) {
              console.log(e)
            }
            ++count
            let amp_diff = this.amp - res.amp
            await this.setSynchPhase()
            await new Promise(r => setTimeout(r, 3000));
            if ((this.cavity_name.includes('cm') && (Math.abs(amp_diff) > sc_cavity_amp_tol)) ||
                (this.cavity_name.includes('buncher') && (Math.abs(amp_diff) > rt_cavity_amp_tol))
            ) {
              Message({
                message: "腔压差了"+amp_diff,
                type: 'info',
                duration: 5 * 1000
              })
            } else {
              break
            }
          }
          const path = '/commissioning/phasescan/finish'
          await request({
            url: path,
            method: 'post',
          })
        }
      }
      this.scan_disabled = false
    },
    async get_amp() {
      const path = '/commissioning/phasescan/get-amp';
      const response = await request({
        url: path,
        method: 'post',
        data: { 'cavity_name':  this.cavity_name }
      })
      this.amp = response.physics_amp
      this.amp_limit = response.amp_limit
    },
    async set_amp() {
      const path = '/commissioning/phasescan/set-amp';
      const response = await request({
        url: path,
        data: { 'amp':  this.amp, 'cavity_name': this.cavity_name },
        method: 'post',
      })
    },
    async scan_per_cavity() {
      let response
      this.clear_figure()
      let start_phase = parseFloat(this.start_phase)
      let stop_phase = parseFloat(this.stop_phase)
      let step = parseFloat(this.scan_step)
      const bpm_read_num = parseInt(this.bpm_read_num)
      const bpm_read_sep = parseFloat(this.bpm_read_sep)
      const cavity_info = this.cavity_infos[this.cavity_name]
      //const cavity_write_pv = cavity_info['phase_write_pv']
      //const cavity_rb_pv = cavity_info['phase_readback_pv']
      //const cavity_ready_pv = cavity_info['ready_pv']
      let phase = start_phase

      //let bpm2_pv = ''
      let path = '/commissioning/phasescan/phase-set';

      let line1_errs = []
      let line2_errs = []

      //if (this.scan_model_selected === "double") {
      //  path = '/commissioning/phasescan/double-bpm-phase-set';
      //  this.chart_option.series[1].name = cavity_info['bpm2_name']
      //}
      this.chart_data[0].name = cavity_info['bpm1_name']
      //const bpm1_pv = cavity_info['bpm1_pv']
      //const bpm2_pv = cavity_info['bpm2_pv']

      //await this.init_pvs({
      //  cavity_name: this.cavity_name,
      //  bpm_mode: this.bpm_model_selected
      //})
      await this.start_monitor()
      let cavity_names = this.cavity_options.map(x=>x.value)
      const cavity_index = cavity_names.indexOf(this.cavity_name)
      const bypass_cavities = cavity_names.slice(cavity_index+1)
      bypass_cavities.forEach((name) => {
        this.lattice[name].amp = 0
      })
      while ((phase < stop_phase)) {

        this.lattice[this.cavity_name].amp = this.amp
        this.lattice[this.cavity_name].phase = phase
        const payload = {
          bpm_mode: this.bpm_mode_selected,
          lattice: this.lattice,
          rf_phase: phase,
          bpm_index: this.bpm_options.map(e=>{return e.value}).indexOf(this.bpm_select),
          bpm_harm: this.bpm_harm_selected,
          cavity_res_time: parseFloat(this.cavity_res_time),
          bpm_read_num: bpm_read_num,
          bpm_read_sep: bpm_read_sep,
          orbit_offset_limit: this.orbit_offset_limit,
          bpm_sum_limit: this.bpm_sum_limit
        }
        try {
          response = await request({
            url: path,
            data: payload,
            method: 'post',
            timeout: 10000
          })
        } catch (e) {
            Message({
              message: e.message+'fuck' || 'Error',
              type: 'error',
              duration: 5 * 1000
            })
            continue
        } finally {
          console.log('finally')
          while (this.pause) {
            await new Promise(r => setTimeout(r, 1000));
          }
          if (this.stop) {
            this.stop_monitor()
            return true
          }
        }
        let point1 = response['point1']
        let point2 = response['point2']

        Plotly.redraw(this.$refs.chart)
        if (this.scan_unready) {
          while (!this.ready && !this.stop) {
            await new Promise(r => setTimeout(r, 1000));
          }
          this.scan_unready = false
          this.fail_times = 0
          if (!this.stop) continue
        }

        this.chart_data[0].x.push(phase)
        this.chart_data[0].y.push(point1['bpm_phase'])
        line1_errs.push(point1['err'])
        if (this.bpm_mode_selected === 'double') {
          this.chart_data[1].x.push(phase)
          this.chart_data[1].y.push(point2['bpm_phase'])
          line2_errs.push(point2['err'])
        }
        phase += step
      }


      path = '/commissioning/phasescan/smoothing';

      let xs = []
      let ys = []

      let y1s = []
      this.chart_data[0].x.forEach(e => {
        xs.push(e)
      })
      this.chart_data[0].y.forEach(e => {
        y1s.push(e)
      })

      ys.push(y1s)

      let errs = []
      errs.push(line1_errs)
      if (this.bpm_mode_selected === "double") {
        let y2s = []
        this.chart_data[1].y.forEach(e => {
          y2s.push(e)
        })
        ys.push(y2s)
        errs.push(line2_errs)
      }
      const payload = {
        'xs': xs,
        'ys': ys,
        'errs': errs,
        'step': step
      }
      response = await request({
        url: path,
        data: payload,
        method: 'post',
      })
      xs = response['xs']
      ys = response['ys']
      const arr_len = xs.length
      this.chart_data[0].x = []
      this.chart_data[0].y = []
      this.chart_data[1].x = []
      this.chart_data[1].y = []
      for (let i=0; i !== arr_len; i++) {
        this.chart_data[0].x.push(xs[i])
        this.chart_data[0].y.push(ys[0][i])
        if (this.bpm_mode_selected === "double") {
          this.chart_data[1].x.push(xs[i])
          this.chart_data[1].y.push(ys[1][i])
          this.chart_data[2].x.push(xs[i])
          this.chart_data[2].y.push(ys[1][i] - ys[0][i])
        }
      }
      Plotly.redraw(this.$refs.chart)
      this.stop_monitor()
      return false
    },
    clear_figure() {
      this.chart_data[0].x = []
      this.chart_data[1].x = []
      this.chart_data[2].x = []
      this.chart_data[3].x = []
      this.chart_data[0].y = []
      this.chart_data[1].y = []
      this.chart_data[2].y = []
      this.chart_data[3].y = []
    },
    onPause() {
      this.pause = !this.pause
      if (this.pause_text === '暂停') {
        this.pause_text = '继续'
      } else {
        this.pause_text = '暂停'
      }
    },
    async curve_fit() {
      this.chart_data[3].x = []
      this.chart_data[3].y = []
      const path = '/commissioning/phasescan/curve-fit'
      let xs = []
      let ys = []
      this.chart_data[0].x.forEach((e, i) => {
        xs.push(e)
        if (this.bpm_mode_selected === "single") {
          ys.push(this.chart_data[0].y[i])
        } else {
          ys.push([this.chart_data[0].y[i], this.chart_data[1].y[i]])
        }
      })
      const payload = {
        'cavity_phases': xs,
        'bpm_phases': ys,
        'Win': parseFloat(this.in_energy),
        'start_phase': parseInt(this.start_phase),
        'm': parseFloat(particle_data[this.particle_type]["mass"]),
        'q': parseInt(particle_data[this.particle_type]["charge"]),
        'cavity_name': this.cavity_name,
        'bpm_mode': this.bpm_mode_selected,
        'bpm_harm': this.bpm_harm_selected === 'single' ? 1: 2,
        'bpm_index': this.bpm_options.map(e => { return e.value }).indexOf(this.bpm_select),
      }
      const response = await request({
        url: path,
        data: payload,
        method: 'post',
      })
      let fit_xs = response['x_plot']
      let fit_ys = response['y_plot']
      for (let i=0; i !== fit_xs.length; i++) {
        let x = fit_xs[i]
        let y = fit_ys[i]
        this.chart_data[3].x.push(x)
        this.chart_data[3].y.push(y)
      }
      Plotly.redraw(this.$refs.chart)
      let fit_record = {}
      fit_record['cavity_name'] = this.cavity_name
      fit_record['phase'] = response.rf_phase.toFixed(2)
      fit_record['energy'] = response.w_out.toFixed(3)
      fit_record['amp'] = response.amp.toFixed(2)
      fit_record['entr_phase'] = response.entr_phase.toFixed(2)
      this.synchPhase = response.rf_phase.toFixed(1)
      this.fit_records.push(fit_record)
      return response
    },
    handle_nav(e) {
      this.stop = true
      e.preventDefault()
      e.returnValue = ""
    }
  },
  beforeMount() {
    window.addEventListener("beforeunload", this.handle_nav)
    this.$once("hook:beforeDestroy", () => {
      window.removeEventListener("beforeunload", this.handle_nav);
    })
  },
  beforeRouteLeave(to, from, next) {

    //if (!window.confirm("确定离开当前窗口吗？")) {
    //  return;
    //}
    this.stop = true
    next()
  },
  async mounted() {
    Plotly.newPlot(this.$refs.chart, this.chart_data, this.layout, this.config)
    this.$refs.chart.on('plotly_selected', (eventData) => {
      if (eventData !== undefined)
        this.selected_points = eventData.points
    })
    await this.load_cavity_infos()
    await this.init_bpm_and_amp()
  },
  watch: {
    ...make_watch_dict([
      'cavity_name',
      'selected',
      'particle_type',
      'in_energy',
      'scan_step',
      'cavity_res_time',
      'bpm_read_num',
      'bpm_read_sep'
    ]),
  }
}
</script>

<style scoped>
.chart {
  height: 600px;
}
.scrollable {
  overflow-y: scroll;
  height: 300px;
}
</style>
