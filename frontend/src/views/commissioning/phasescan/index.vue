<template>
  <el-container>
    <el-header>
      <h3>扫相</h3>
    </el-header>
    <el-main>
      <el-row :gutter="40">
        <el-col :span="8">
          <el-form  @submit.prevent="onSubmit" enctype="multipart/form-data" size="mini">
            <el-form-item label="扫相模式">
              <el-radio-group v-model="selected">
                <el-radio v-for="item in options"
                          :label="item.value"
                          :key="item.value">
                  {{item.name}}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="BPM模式">
              <el-radio-group v-model="bpm_model_selected">
                <el-radio v-for="item in bpm_model_options"
                          :label="item.value"
                          :key="item.value">
                  {{item.name}}
                </el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="粒子种类">
              <el-select v-model="particle_type">
                <el-option
                    v-for="item in particle_options"
                    :key="item.text"
                    :label="item.text"
                    :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="入口全能量[MeV]">
              <el-col :span="8">
                <el-input v-model="in_energy"></el-input>
              </el-col>
            </el-form-item>
            <el-form-item label="腔体序号">
              <el-select v-model="cavity_name" @change="init_bpm_and_amp">
                <el-option
                    v-for="item in cavity_options"
                    :key="item.text"
                    :label="item.text"
                    :value="item.value">
                </el-option>
              </el-select>
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
              <el-row align="center">
                <el-col :span="12">
                  <label>读取腔后BPM相位</label>
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
                  <el-button>
                    <i class="fa fa-angle-double-left"></i>
                  </el-button>
                </el-col>
                <el-col :span="6">
                  <el-button>
                    <i class="fa fa-angle-double-right"></i>
                  </el-button>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item>
              <el-row type="flex" justify="end">
                <el-col :span="5">
                  <el-button  type="primary" @click="start_scan" :disabled="scan_disabled">开始</el-button>
                </el-col>
                <el-col :span="5">
                  <el-button  type="warning" @click="onPause">{{ pause_text }}</el-button>
                </el-col>
                <el-col :span="5">
                  <el-button type="danger" @click="stop=true">停止</el-button>
                </el-col>
              </el-row>
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="16">
          <v-chart class="chart"
                   :option="chart_option"
                   @brushEnd="point_select"
          />
          <div class="scrollable">
            <fit-report v-for="(record, i) in fit_records" :key="record.cavity_name + i"
                       :cavity_name="record.cavity_name"
                       :fit_phase="record.phase"
                       :fit_amp="record.amp"
                       :fit_energy="record.energy"
            ></fit-report>
          </div>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script>
import fit_icon from "@/assets/fit.svg";
import move_up_icon from "@/assets/move-up.svg";
import move_down_icon from "@/assets/move-down.svg";
import delete_icon from "@/assets/delete.svg";

import { Message } from 'element-ui'
import request from '@/utils/request'
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
  BrushComponent
} from "echarts/components";

import VChart  from "vue-echarts";
import FitReport from "@/components/FitReport/index"

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent,
  BrushComponent
]);

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
  }
}
export default {
  components: {
    VChart,
    FitReport
  },
  data() {
    return {
      particle_type: "Proton",
      particle_options: [
        {value: "Proton", text: "Proton"},
        {value: "36Ar12+", text: "36Ar12+"},
        {value: "40Ar13+", text: "40Ar13+"},
      ],
      in_energy: 4,
      cavity_name: '',
      cavity_options: [],
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
      bpm_model_options: [
        {value: 'single', name: '单BPM扫相'},
        {value: 'double', name: '双BPM扫相'}
      ],
      selected: 'manual',
      bpm_model_selected: 'double',
      amp_limit_file: null,
      amp_limit: 0,
      amp: 0,
      phase: 0,
      synchPhase: 0,
      lattice: {},
      stop: false,
      bpm_phase: 0,
      pause: false,
      pause_text: '暂停',
      monitor: true,
      ready: false,
      scan_unready: false,
      scan_disabled: false,
      fit_records: [],
      coordRange: {},
      chart_option: {
        title: {
          text: "腔体相位 vs BPM相位",
          left: "center"
        },
        tooltip: {
          trigger: "axis",
        },
        legend: {
          orient: "vertical",
          left: "right",
          data: []
        },
        xAxis: {
          name: '腔体相位 [deg]',
          nameLocation: "middle",
          nameGap: 30,
          scale: true,
          position: "bottom"
        },
        yAxis: {
          name: 'BPM相位 [deg]',
          nameLocation: "middle",
          nameGap: 50,
          scale: true,
          position: "left",
        },
        toolbox: {
          show: true,
          feature: {
            saveAsImage: {},
            myCurveFit: {
              show: true,
              title: 'curve fit',
              icon: "image://" + fit_icon + "",
              onclick: async () => {
                let res = await this.curve_fit()
                this.synchPhase = res.rf_phase.toFixed(1)
              }
            },
            myMoveUp: {
              show: true,
              title: 'move up 360deg',
              icon: "image://" + move_up_icon + "",
              onclick: () => {
                this.process_points('move_up')
              },
            },
            myMoveDown: {
              show: true,
              title: 'move up 360deg',
              icon: "image://" + move_down_icon + "",
              onclick: () => {
                this.process_points('move_down')
              }
            },
            myDelete: {
              show: true,
              title: 'delete',
              icon: "image://" + delete_icon + "",
              onclick: () => {
                this.process_points('delete')
              }
            }
            }
          },
        brush: {
          toolbox: ['rect'],
          xAxisIndex: 0
        },
        series: [
          {
            name: "",
            type: "line",
            data: [],
          },
          {
            name: "",
            type: "line",
            data: []
          },
          {
            name: "",
            type: "line",
            data: [],
          },
          {
            name: "",
            type: "line",
            data: [],
          }
        ]
      }

    }
  },
  methods: {
    async init_bpm_and_amp() {
      this.bpm_model_selected = this.cavity_infos[this.cavity_name]['bpm_mode']
      await this.init_pvs({
        cavity_name: this.cavity_name,
        bpm_mode: this.bpm_model_selected
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
    },
    point_select(params) {
      if (params.areas.length !== 0) {
        this.coordRange = params.areas[0].coordRange
      }
    },
    async setSynchPhase() {
      this.lattice[this.cavity_name].phase = this.synchPhase
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
    process_points(kind) {
      let exit_loop = false
      this.chart_option.series.every((s, index) => {
        if (exit_loop) {
          return false
        }
        if ([0, 1].includes(index)) {
          let h_coord_range = this.coordRange[0]
          let v_coord_range = this.coordRange[1]
          s.data.forEach((e, i, arr) => {
            if ((e[0] > h_coord_range[0]) && (e[0] < h_coord_range[1]) &&
                (e[1] > v_coord_range[0]) && (e[1] < v_coord_range[1])) {
              switch (kind) {
                case 'move_up': {
                  arr.splice(i, 1, [e[0], e[1] + 360])
                  break
                }
                case 'move_down': {
                  arr.splice(i, 1, [e[0], e[1] - 360])
                  break
                }
                default: {
                  let series_array = [0, 1, 2]
                  series_array.forEach(series_index => {
                    if (this.chart_option.series[series_index].data.length !== 0) {
                      this.chart_option.series[series_index].data.splice(i, 1)
                    }
                  })
                  exit_loop = true
                }
              }
            }
          })
        }
        return true
      })
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

      console.log(response['lattice'])
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
      this.bpm_model_selected = this.cavity_infos[this.cavity_name]['bpm_mode']
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
      if (!this.ready) this.scan_unready = true
      return res
    },
    //async start_monitor(millisec) {
    //  const path = '/commissioning/phasescan/get-status'
    //  let self = this.monitor
    //  await this.fetch_ready_status(path)
    //  async function interval()  {
    //    if (self.monitor) {
    //      setTimeout(interval, millisec);
    //      await this.fetch_ready_status(path)
    //    }
    //  }
    //  setTimeout(interval, millisec)
    //},

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
      //await this.get_amp()

      if (this.selected === "manual")  {
        let exit_scan = await this.one_cavity_scan()
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
          await this.init_pvs({
            cavity_name: this.cavity_name,
            bpm_mode: this.bpm_model_selected
          })

          let count = 0
          while (count < 3) {
            //await this.get_amp()
            if (this.amp > this.amp_limit) {
              this.amp = this.amp_limit
              Message({
                message: "所需腔压超过Epeak阈值了",
                type: 'info',
                duration: 5 * 1000
              })
            }
            this.cavity_name = cav.value
            let exit_scan = await this.one_cavity_scan()
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
    async one_cavity_scan() {
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
      this.chart_option.series[0].name = cavity_info['bpm1_name']
      //const bpm1_pv = cavity_info['bpm1_pv']
      //const bpm2_pv = cavity_info['bpm2_pv']

      //await this.init_pvs({
      //  cavity_name: this.cavity_name,
      //  bpm_mode: this.bpm_model_selected
      //})
      await this.start_monitor()
      while ((phase < stop_phase)) {
        this.lattice[this.cavity_name].amp = this.amp
        this.lattice[this.cavity_name].phase = phase
        const payload = {
          bpm_model: this.bpm_model_selected,
          lattice: this.lattice,
          //amp: this.amp,
          //phase: phase,
          //cavity_write_pv: cavity_write_pv,
          //cavity_rb_pv: cavity_rb_pv,
          //cavity_ready_pv: cavity_ready_pv,
          //bpm1_phase_pv: bpm1_pv,
          //bpm2_phase_pv: bpm2_pv,
          cavity_res_time: parseFloat(this.cavity_res_time),
          bpm_read_num: bpm_read_num,
          bpm_read_sep: bpm_read_sep
        }
        const response = await request({
          url: path,
          data: payload,
          method: 'post',
        })
        let point1 = response['point1']
        let point2 = response['point2']

        if (this.scan_unready) {
          while (!this.ready && !this.stop) {
            await new Promise(r => setTimeout(r, 1000));
          }
          this.scan_unready = false
          if (!this.stop) continue
        }

        this.chart_option.series[0].data.push([phase, point1['bpm_phase']])
        line1_errs.push(point1['err'])
        if (this.bpm_model_selected === 'double') {
          this.chart_option.series[1].data.push([phase, point2['bpm_phase']])
          line2_errs.push(point2['err'])
        }
        phase += step
        while (this.pause) {
          await new Promise(r => setTimeout(r, 1000));
        }
        if (this.stop) {
          this.stop_monitor()
          return true
        }
      }


      path = '/commissioning/phasescan/smoothing';

      let xs = []
      let ys = []

      let y1s = []
      this.chart_option.series[0].data.forEach(e => {
        xs.push(e[0])
        y1s.push(e[1])
      })

      ys.push(y1s)

      let errs = []
      errs.push(line1_errs)
      if (this.bpm_model_selected === "double") {
        let y2s = []
        this.chart_option.series[1].data.forEach(e => {
          y2s.push(e[1])
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
      const response = await request({
        url: path,
        data: payload,
        method: 'post',
      })
      xs = response['xs']
      ys = response['ys']
      const arr_len = xs.length
      this.chart_option.series[0].data = []
      this.chart_option.series[1].data = []
      for (let i=0; i !== arr_len; i++) {
        this.chart_option.series[0].data.push([xs[i], ys[0][i]])
        if (this.bpm_model_selected === "double") {
          this.chart_option.series[1].data.push([xs[i], ys[1][i]])
          this.chart_option.series[2].data.push([xs[i], ys[1][i] - ys[0][i]])
        }
      }
      this.stop_monitor()
      return false
    },
    clear_figure() {
      this.chart_option.series[0].data = []
      this.chart_option.series[1].data = []
      this.chart_option.series[2].data = []
      this.chart_option.series[3].data = []
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
      this.chart_option.series[3].data = []
      const path = '/commissioning/phasescan/curve-fit'
      let xs = []
      let ys = []
      this.chart_option.series[0].data.forEach((e, i) => {
        xs.push(e[0])
        if (this.bpm_model_selected === "single") {
          ys.push(e[1])
        } else {
          ys.push([this.chart_option.series[0].data[i][1],
            this.chart_option.series[1].data[i][1]])
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
        'bpm_model': this.bpm_model_selected
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
        this.chart_option.series[3].data.push([x, y])
      }
      let fit_record = {}
      fit_record['cavity_name'] = this.cavity_name
      fit_record['phase'] = response.rf_phase.toFixed(2)
      fit_record['energy'] = response.w_out.toFixed(3)
      fit_record['amp'] = response.amp.toFixed(2)
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
    if (!window.confirm("确定离开当前窗口吗？")) {
      return;
    }
    this.stop = true
    next()
  },
  async mounted() {
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