import { format, parseISO } from 'date-fns'

export default {
  name: 'local-datetime',

  props: {
    timestamp: String,
    format: {
      type: String,
      default: 'MMM d yyyy H:mm',
    },
  },

  computed: {
    displayTime: function () {
      return format(parseISO(this.timestamp), this.format)
    },
  },

  template: '<time v-bind:datetime="timestamp">{{ displayTime }}</time>',
}
