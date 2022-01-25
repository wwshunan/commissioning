<template>
    <div class="container">
        <FlashMessage :position="'right bottom'"></FlashMessage>
        <div class="page-header">
            <h3>TOF能量计算</h3>
        </div>
        <form class="md-form">
            <div class="form-group">
                <label for="tof">TOF (ns)</label><br/>
                <b-form-input v-model="tof" placeholder="Enter tof"></b-form-input>
                <label for="distance">Distance (m)</label><br/>
                <b-form-input v-model="distance"></b-form-input>
                <b-button variant="secondary mt-2"
                          @click.prevent="energy_compute">计算</b-button>
            </div>
            <div class="form-group">
                <p>能量: {{energy}} (MeV)</p>
            </div>
        </form>
    </div>
</template>

<script>
    import axios from 'axios';
    export default {
        data() {
            return {
                energy: 0,
                tof: '',
                distance: '0.61351'
            }
        },
        methods: {
            async energy_compute() {
                const path = 'http://127.0.0.1:5000/commissioning/energy-compute';
                const payload = {
                    'tof': this.tof,
                    'distance': this.distance
                };
                try {
                    const response = await axios.post(path, payload);
                    if ('energy' in response.data) {
                        this.energy = response.data['energy'];
                    } else {
                        this.flashMessage.error({
                                title: '错误',
                                message: '同志，超光速了！！！'
                        })
                    }
                } catch (e) {
                    this.energy = 'Failure';
                }
            },
        },
    }
</script>