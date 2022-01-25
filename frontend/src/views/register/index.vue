<template>
  <div class="login-container">
    <el-form ref="registerForm" :model="registerForm" :rules="registerRules"
             class="login-form" auto-complete="on" labe-position="left">

      <div class="title-container">
        <h3 class="title">Register Form</h3>
      </div>

      <el-form-item prop="username">
        <span class="svg-container">
          <svg-icon icon-class="user" />
        </span>
        <el-input
          ref="username"
          v-model="registerForm.username"
          placeholder="用户名"
          name="username"
          type="text"
          tabindex="1"
          auto-complete="on"
        />
      </el-form-item>

      <el-form-item prop="email">
        <span class="svg-container">
          <svg-icon icon-class="email" />
        </span>
        <el-input
            ref="email"
            v-model="registerForm.email"
            placeholder="邮件"
            name="email"
            type="text"
            tabindex="1"
            auto-complete="on"
        />
      </el-form-item>

      <el-form-item prop="verifyCode">
        <span class="svg-container">
          <svg-icon icon-class="verify-code" />
        </span>
        <el-input
            ref="verifyCode"
            class="verify-code"
            v-model="registerForm.verifyCode"
            placeholder="验证码"
            type="text"
            name="verifyCode"
            tabindex="1"
            auto-complete="on"
        />
        <el-button type="primary" style="float: right" @click="sendCode">发送验证码</el-button>
      </el-form-item>
      <el-form-item prop="password">
        <span class="svg-container">
          <svg-icon icon-class="password" />
        </span>
        <el-input
          :key="passwordType"
          ref="password"
          v-model="registerForm.password"
          :type="passwordType"
          placeholder="密码"
          name="password"
          tabindex="2"
          auto-complete="on"
          @keyup.enter.native="handleRegister"
        />
        <span class="show-pwd" @click="showPwd">
          <svg-icon :icon-class="passwordType === 'password' ? 'eye': 'eye-open'"/>
        </span>
      </el-form-item>

      <el-button :loading="loading" type="primary" style="width:100%;margin-bottom:30px;" @click.native.prevent="handleRegister">注册</el-button>

    </el-form>
  </div>
</template>

<script>
import { validEmail } from '@/utils/validate'
import { register, send_verify_code } from '@/api/user'

export default {
  name: 'Login',
  data() {
    const validateUsername = (rule, value, callback) => {
      if (value.length < 1) {
        callback(new Error('用户名不能为空'))
      } else {
        callback()
      }
    }
    const validateVerifyCode = (rule, value, callback) => {
      if (value.length < 1) {
        callback(new Error('验证码不能为空'))
      } else {
        callback()
      }
    }
    const validateEmail = (rule, value, callback) => {
      if (!validEmail(value)) {
        callback(new Error('请输入所里邮箱'))
      } else {
        callback()
      }
    }
    const validatePassword = (rule, value, callback) => {
      if (value.length < 6) {
        callback(new Error('密码必须大于6位'))
      } else {
        callback()
      }
    }
    return {
      registerForm: {
        username: '',
        email: '',
        password: '',
        verifyCode: ''
      },
      registerRules: {
        username: [{required: true, trigger: 'blur', validator: validateUsername}],
        email: [{required: true, trigger: 'blur', validator: validateEmail}],
        verifyCode: [{required: true, trigger: 'blur', validator: validateVerifyCode}],
        password: [{required: true, trigger: 'blur', validator: validatePassword}]
      },
      loading: false,
      passwordType: 'password',
      redirect: undefined
    }
  },
  watch: {
    $route: {
      handler: function (route) {
        this.redirect = route.query && route.query.redirect
      },
      immediate: true
    }
  },
  methods: {
    showPwd() {
      if (this.passwordType === 'password') {
        this.passwordType = ''
      } else {
        this.passwordType = 'password'
      }
      this.$nextTick(() => {
        this.$refs.password.focus()
      })
    },
    async sendCode () {
      if (this.registerForm.email.endsWith('@impcas.ac.cn')) {
        try {
          const res = await send_verify_code({ email: [this.registerForm.email] })
          this.$message.success(res.message)
        } catch (err) {
          console.log(err)
        }
      } else {
        this.$message.warning("邮箱地址错误")
      }
    },
    handleRegister() {
      this.$refs.registerForm.validate(async valid => {
        if (valid) {
          this.loading = true
          try {
            const { username, email, password, verifyCode } = this.registerForm
            const res = await register({
              username: username.trim(),
              email: email,
              password: password,
              verify_code: verifyCode
            })
            this.$message.success(res.message)
            this.$router.push({path: '/login'})
          } catch (err) {
            console.log(err)
          }
          this.loading = false
        } else {
          this.$message.error("提交内容不正确")
          return false
        }
      })
    }
  }
}
</script>

<style lang="scss">
/* 修复input 背景不协调 和光标变色 */
/* Detail see https://github.com/PanJiaChen/vue-element-admin/pull/927 */

$bg:#283443;
$light_gray:#fff;
$cursor: #fff;

@supports (-webkit-mask: none) and (not (cater-color: $cursor)) {
  .login-container .el-input input {
    color: $cursor;
  }
}

/* reset element-ui css */
.login-container {
  .el-input {
    display: inline-block;
    height: 47px;
    width: 85%;

    input {
      background: transparent;
      border: 0px;
      -webkit-appearance: none;
      border-radius: 0px;
      padding: 12px 5px 12px 15px;
      color: $light_gray;
      height: 47px;
      caret-color: $cursor;

      &:-webkit-autofill {
        box-shadow: 0 0 0px 1000px $bg inset !important;
        -webkit-text-fill-color: $cursor !important;
      }
    }
  }

  .el-form-item {
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.1);
    border-radius: 5px;
    color: #454545;
    .verify-code {
      width: 60%;
    }
    .el-button {
      display: inline-block;
      height: 47px;
      width: 25%
    }
  }
}
</style>

<style lang="scss" scoped>
$bg:#2d3a4b;
$dark_gray:#889aa4;
$light_gray:#eee;

.login-container {
  min-height: 100%;
  width: 100%;
  background-color: $bg;
  overflow: hidden;

  .login-form {
    position: relative;
    width: 520px;
    max-width: 100%;
    padding: 160px 35px 0;
    margin: 0 auto;
    overflow: hidden;
  }

  .tips {
    font-size: 14px;
    color: #fff;
    margin-bottom: 10px;

    span {
      &:first-of-type {
        margin-right: 16px;
      }
    }
  }

  .svg-container {
    padding: 6px 5px 6px 15px;
    color: $dark_gray;
    vertical-align: middle;
    width: 30px;
    display: inline-block;
  }

  .title-container {
    position: relative;

    .title {
      font-size: 26px;
      color: $light_gray;
      margin: 0px auto 40px auto;
      text-align: center;
      font-weight: bold;
    }
  }

  .show-pwd {
    position: absolute;
    right: 10px;
    top: 7px;
    font-size: 16px;
    color: $dark_gray;
    cursor: pointer;
    user-select: none;
  }
}
</style>
