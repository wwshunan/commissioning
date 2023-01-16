<template>
  <div>
    <h5>{{ this.cavity_name }}</h5>
    <div>入口相位： {{this.fit_entr_phase}} 同步RF相位：{{ this.fit_phase }}     幅值：{{ this.fit_amp }}     出口能量：{{ this.fit_energy }}</div>
    <br/>
  </div>
</template>

<script>
export default {
  name: 'fit-report',
  props: ['cavity_name', 'fit_entr_phase', 'fit_phase', 'fit_amp', 'fit_energy'],
}
</script>

