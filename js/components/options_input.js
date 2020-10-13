import { emitFieldChange } from '../lib/emitters'

export default {
  name: 'optionsinput',

  props: {
    name: String,
    initialErrors: {
      type: Array,
      default: () => [],
    },
    initialValue: {
      type: String,
      default: '',
    },
    optional: Boolean,
    nullOption: {
      type: String,
      default: '',
    },
  },

  data: function () {
    return {
      validationError: this.initialErrors.join(' '),
      value: this.initialValue,
      modified: false,
    }
  },

  methods: {
    onInput: function (changeEvent) {
      this.value = changeEvent.srcElement.value
      this.modified = true
      emitFieldChange(this)
    },

    _isValid: function (value) {
      return this.optional || value !== this.nullOption
    },
  },

  computed: {
    valid: function () {
      return this._isValid(this.value)
    },
    showError: function () {
      const showError = this.initialErrors && this.initialErrors.length
      return showError || (this.modified && !this.valid)
    },
    showValid: function () {
      return this.modified && this.valid
    },
  },
}
