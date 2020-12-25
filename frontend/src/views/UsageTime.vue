<template>
    <div class="container">
        <div class="page-header">
            <h3>统计束流时间</h3>
        </div>
        <b-alert v-show="showMessage">{{message}}</b-alert>
        <form class="md-form" @submit.prevent="onSubmit">
            <div class="form-group">
                <label>当前班次时间统计</label><br/>
                <button type="submit" class="btn btn-primary mb-2"
                        @click.prevent="onInterrupt">提交</button>
            </div>
            <div class="form-group">
                <label class="col-form-label">历史束流时间统计</label>
                <div class="row">
                    <div class="form-group col-auto">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-calendar"></span></span>
                            </div>
                            <datetime type="datetime" placeholder="From date   " v-model="startDate">
                            </datetime>
                        </div>
                    </div>
                    <div class="form-group col-auto">
                        <div class="input-group">
                            <div class="input-group-prepend">
                                <span class="input-group-text"><span class="fas fa-calendar"></span></span>
                            </div>
                            <datetime type="datetime" placeholder="To date   " v-model="toDate">
                            </datetime>
                        </div>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary" @click.prevent="onQuery">查询</button>
            </div>
        </form>
        <p>用束结果:</p>
        <table class="table" v-if="shiftCount">
            <thead>
                <tr>
                    <th scope="col">Duty Factor (%)</th>
                    <th scope="col">Beam Time (hrs)</th>
                    <th scope="col">ACCT1 (mA)</th>
                    <th scope="col">ACCT2 (mA)</th>
                    <th scope="col">ACCT3 (mA)</th>
                    <th scope="col">ACCT4 (mA)</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="(values, duty_factor) in usage_time" :key="duty_factor">
                    <th scope="row">{{duty_factor}}</th>
                    <td v-for="(value, name) in values"
                        :key="name">{{value}}</td>
                </tr>
            </tbody>
        </table>
        <table class="table" v-else>
            <thead>
            <tr>
                <th scope="col">Date</th>
                <th scope="col">Duty Factor (%)</th>
                <th scope="col">Beam Time (hrs)</th>
                <th scope="col">ACCT1 (mA)</th>
                <th scope="col">ACCT2 (mA)</th>
                <th scope="col">ACCT3 (mA)</th>
                <th scope="col">ACCT4 (mA)</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="item in usage_time" :key="item.timestamp">
                <td v-for="(value, name) in item"
                    :key="name">{{value}}</td>
            </tr>
            </tbody>
        </table>
    </div>
</template>

<script>
    import axios from 'axios';
    import { Datetime } from 'vue-datetime';

    export default {
        data() {
            return {
                usage_time: 0,
                showMessage: false,
                shiftCount: true,
                message: '',
                startDate: '',
                toDate: '',
            }
        },
        components: {
            datetime: Datetime
        },
        methods: {
            async onStart() {
                const path = 'http://127.0.0.1:5000/log/start';
                this.showMessage = true;
                try {
                    const response = await axios.post(path);
                    this.message = response.data['status'];
                    this.startBtnDisabled = true;
                    this.stopBtnDisabled = false;
                } catch (e) {
                    this.message = 'Failure';
                }
            },
            async onInterrupt() {
                const path = 'http://127.0.0.1:5000/log/interrupt';
                this.showMessage = true;
                try {
                    const response = await axios.get(path);
                    this.usage_time = response.data['usage_time'];
                    this.message = "Success";
                    this.startBtnDisabled = false;
                    this.stopBtnDisabled = true;
                    this.shiftCount = true;
                } catch (e) {
                    this.message = 'Failure';
                }
            },
            async onQuery() {
                const path = 'http://127.0.0.1:5000/log/time-query';
                const payLoad = {
                    'startDate': this.startDate,
                    'toDate': this.toDate
                };
                try {
                    const response = await axios.post(path, payLoad);
                    this.showMessage = true;
                    this.shiftCount = false;
                    this.message = 'Beam time query successfully!';
                    this.usage_time = response.data['usage_time'];
                } catch (e) {
                    this.message = "Failure";
                }
            }
        },
    }
</script>