<template>
    <div class="container">
        <div class="page-header">
            <h3>统计束流时间</h3>
        </div>
        <b-alert :show="showMessage">{{message}}</b-alert>
        <form class="md-form" @submit.prevent="onSubmit">
            <div class="form-group">
                <label>Start</label><br/>
                <button type="submit" class="btn btn-primary mb-2"
                        :disabled="startBtnDisabled" @click.prevent="onStart">Submit</button>
            </div>
            <div class="form-group">
                <label>Stop</label><br/>
                <button type="submit" class="btn btn-primary mb-2"
                        :disabled="stopBtnDisabled" @click.prevent="onStop">Submit</button>
            </div>
        </form>
        <p>Beam usage time {{usage_time}} hours</p>
    </div>
</template>

<script>
    import axios from 'axios';
    export default {
        data() {
            return {
                usage_time: 0,
                showMessage: false,
                message: '',
                startBtnDisabled: false,
                stopBtnDisabled: true,
            }
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
            async onStop() {
                const path = 'http://127.0.0.1:5000/log/stop';
                this.showMessage = true;
                try {
                    const response = await axios.get(path);
                    this.usage_time = response.data['usage_time'];
                    this.message = "Success";
                    this.startBtnDisabled = false;
                    this.stopBtnDisabled = true;
                } catch (e) {
                    this.message = 'Failure';
                }
            }
        },
    }
</script>