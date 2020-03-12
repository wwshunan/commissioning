<template>
    <div class="container">
        <div class="page-header">
            <h3>加速器硬件参数设置</h3>
        </div>
        <br/>
        <b-alert :show="showMessage">{{message}}</b-alert>
        <div class="file">
            <form class="md-form" @submit.prevent="onSubmit" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Upload TraceWin Lattice File</label><br/>
                    <div class="file-field">
                        <a class="btn-floating purple-gradient mt-0 float-left">
                            <i class="fas fa-cloud-upload-alt" aria-hidden="true"></i>
                            <input type="file" ref="file" @change="onSelect">
                        </a>
                        <button @click="onSubmit">Submit</button>
                    </div>
                </div>
            </form>

        </div>
    </div>
</template>

<script>
    import axios from 'axios';

    export default {
        data() {
            return {
                showMessage: false,
                message: '',
                file: ''
            }
        },
        methods: {
            onSelect(e) {
                this.file = e.target.files[0];
            },
            async onSubmit() {
                const path = 'http://127.0.0.1:5000/lattice-setting';
                let formData = new FormData();
                formData.append('file', this.file);
                try {
                    const response = await axios.post(path, formData);
                    this.showMessage = true;
                    const data = response.data;
                    this.message = data['name'];
                }
                catch (err) {
                    this.message = 'Error';
                    this.showMessage = true;
                }
            }
        },

    }
</script>